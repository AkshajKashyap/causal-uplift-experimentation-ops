"""Deterministic staging promotion gates for a frozen policy artifact."""

from __future__ import annotations

from dataclasses import dataclass

from causal_uplift_experimentation_ops.monitoring.health import (
    OperationalHealthSummary,
)


@dataclass(frozen=True)
class PromotionDecision:
    """Promotion decision, supporting reasons, and the next safe action."""

    decision: str
    reasons: tuple[str, ...]
    recommended_action: str


def evaluate_promotion(
    health: OperationalHealthSummary,
    *,
    synthetic_only: bool = True,
    accept_simulated_trial: bool = False,
) -> PromotionDecision:
    """Decide whether to promote, hold, or roll back a staging artifact.

    Drift, artifact-identity, audit, and trial-guardrail failures trigger rollback.
    Missing evidence and insufficient operational evidence trigger a hold. Synthetic
    validation is never treated as production approval unless the caller explicitly
    accepts the simulated trial for a further staging-only promotion.
    """
    required_columns = {"check", "status", "details"}
    missing = sorted(required_columns - set(health.checks.columns))
    if missing:
        raise ValueError(f"Missing operational health columns: {', '.join(missing)}")

    checks = health.checks.set_index("check")
    rollback_checks = {
        "input_drift",
        "prediction_drift",
        "audit_log",
        "artifact_version_consistency",
        "prospective_trial_guardrails",
    }
    trial_report_missing = (
        "prospective_trial_report" in checks.index
        and checks.loc["prospective_trial_report", "status"] == "fail"
    )
    rollback_reasons = tuple(
        str(row["details"])
        for name, row in checks.iterrows()
        if name in rollback_checks
        and row["status"] == "fail"
        and not (name == "prospective_trial_guardrails" and trial_report_missing)
    )
    if rollback_reasons:
        return PromotionDecision(
            decision="rollback",
            reasons=rollback_reasons,
            recommended_action=(
                "Stop using this staging candidate, investigate the failed checks, "
                "and restore the last known-good artifact."
            ),
        )

    hold_reasons: list[str] = []
    for name, row in checks.iterrows():
        if row["status"] == "fail":
            hold_reasons.append(str(row["details"]))
        elif name in {"audit_log", "artifact_version_consistency"} and (
            row["status"] == "warn"
        ):
            hold_reasons.append(str(row["details"]))

    if synthetic_only and not accept_simulated_trial:
        hold_reasons.append(
            "Evidence is synthetic-only; a real pre-registered randomized trial "
            "is required before production promotion."
        )

    if hold_reasons:
        return PromotionDecision(
            decision="hold",
            reasons=tuple(dict.fromkeys(hold_reasons)),
            recommended_action=(
                "Keep the artifact in offline/staging use and resolve the listed "
                "evidence or health gaps before another promotion review."
            ),
        )

    return PromotionDecision(
        decision="promote",
        reasons=(
            "All required staging evidence and operational promotion checks passed.",
        ),
        recommended_action=(
            "Promote only to the next controlled staging phase; this decision is "
            "not production approval."
        ),
    )
