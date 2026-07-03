"""Combine drift, audit, artifact, and evidence checks into operational health."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.monitoring.audit import AuditLogSummary
from causal_uplift_experimentation_ops.monitoring.drift import (
    PredictionDriftResult,
    worst_severity,
)


@dataclass(frozen=True)
class OperationalHealthSummary:
    """Structured staging health checks and recommended response."""

    overall_status: str
    pass_count: int
    warn_count: int
    fail_count: int
    checks: pd.DataFrame
    blocking_issues: tuple[str, ...]
    non_blocking_warnings: tuple[str, ...]
    recommended_action: str


def _trial_guardrail_status(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "fail", f"Prospective trial report is missing: {path}"
    content = path.read_text(encoding="utf-8")
    if "## Final randomized trial estimates" not in content:
        return "warn", "Prospective trial final-estimate section could not be parsed."
    final_section = content.split("## Final randomized trial estimates", 1)[1]
    final_section = final_section.split("## MDE and power planning", 1)[0]
    if "| FAIL |" in final_section:
        return "fail", "At least one final prospective-trial guardrail failed."
    if "| PASS |" in final_section:
        return "pass", "Final simulated prospective-trial guardrails are marked PASS."
    return "warn", "No structured final trial guardrail status was found."


def build_operational_health(
    input_drift: pd.DataFrame,
    prediction_drift: PredictionDriftResult,
    audit_summary: AuditLogSummary,
    *,
    artifact_directory: Path | str = "artifacts/policy_bundle",
    policy_card_path: Path | str = "reports/policy_card.md",
    preregistration_path: Path | str = "reports/experiment_preregistration.md",
    prospective_trial_path: Path | str = "reports/prospective_policy_trial.md",
) -> OperationalHealthSummary:
    """Build deterministic staging checks from monitoring and evidence artifacts."""
    required_drift_columns = {"severity", "notes"}
    missing = sorted(required_drift_columns - set(input_drift.columns))
    if missing:
        raise ValueError(f"Missing input drift columns: {', '.join(missing)}")
    records: list[dict[str, object]] = []

    def add_check(name: str, status: str, details: str, blocking: bool) -> None:
        records.append(
            {
                "check": name,
                "status": status,
                "details": details,
                "blocking": blocking,
            }
        )

    input_status = worst_severity(input_drift["severity"])
    input_findings = input_drift.loc[
        input_drift["severity"] != "pass",
        ["feature", "metric_name"],
    ]
    input_details = (
        "Non-pass metrics: "
        + ", ".join(
            f"{row.feature}.{row.metric_name}"
            for row in input_findings.itertuples(index=False)
        )
        if not input_findings.empty
        else f"{len(input_drift)} input drift metrics evaluated."
    )
    add_check(
        "input_drift",
        input_status,
        input_details,
        input_status == "fail",
    )
    prediction_findings = prediction_drift.metrics.loc[
        prediction_drift.metrics["severity"] != "pass",
        "metric_name",
    ]
    prediction_details = (
        "Non-pass metrics: " + ", ".join(prediction_findings.astype(str))
        if not prediction_findings.empty
        else f"{len(prediction_drift.metrics)} prediction metrics evaluated."
    )
    add_check(
        "prediction_drift",
        prediction_drift.status,
        prediction_details,
        prediction_drift.status == "fail",
    )
    add_check(
        "audit_log",
        audit_summary.status,
        (
            "; ".join(audit_summary.warnings)
            if audit_summary.warnings
            else f"{audit_summary.metrics['total_events']} audit events analyzed."
        ),
        audit_summary.status == "fail",
    )

    artifact_path = Path(artifact_directory)
    manifest_path = artifact_path / "manifest.json"
    manifest: dict[str, object] | None = None
    if not manifest_path.exists():
        add_check(
            "artifact_manifest",
            "fail",
            f"Artifact manifest is missing: {manifest_path}",
            True,
        )
    else:
        try:
            value = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            manifest = None
        add_check(
            "artifact_manifest",
            "pass" if manifest else "fail",
            (
                f"Artifact manifest loaded from {manifest_path}."
                if manifest
                else "Artifact manifest is not valid JSON metadata."
            ),
            manifest is None,
        )

    if manifest is not None:
        expected_version = str(manifest.get("artifact_version"))
        seen_versions = audit_summary.metrics.get("artifact_versions_seen", [])
        mismatch = bool(seen_versions) and set(seen_versions) != {expected_version}
        identity_missing = (
            int(audit_summary.metrics.get("total_events", 0)) > 0
            and not seen_versions
        )
        add_check(
            "artifact_version_consistency",
            "fail" if mismatch else "warn" if identity_missing else "pass",
            (
                f"Audit versions {seen_versions} do not match {expected_version}."
                if mismatch
                else "Audit events did not identify an artifact version."
                if identity_missing
                else f"Observed artifact versions are consistent with {expected_version}."
            ),
            mismatch,
        )

    for check_name, raw_path in (
        ("policy_card", policy_card_path),
        ("experiment_preregistration", preregistration_path),
        ("prospective_trial_report", prospective_trial_path),
    ):
        path = Path(raw_path)
        exists = path.exists()
        add_check(
            check_name,
            "pass" if exists else "fail",
            f"{'Found' if exists else 'Missing'} required evidence: {path}",
            not exists,
        )
    guardrail_status, guardrail_details = _trial_guardrail_status(
        Path(prospective_trial_path)
    )
    add_check(
        "prospective_trial_guardrails",
        guardrail_status,
        guardrail_details,
        guardrail_status == "fail",
    )
    add_check(
        "synthetic_validation_scope",
        "warn",
        "All model, policy, and prospective evidence remains synthetic-only.",
        False,
    )

    checks = pd.DataFrame.from_records(records)
    counts = checks["status"].value_counts()
    overall_status = worst_severity(checks["status"])
    blocking_issues = tuple(
        checks.loc[
            (checks["status"] == "fail") & checks["blocking"],
            "details",
        ].astype(str)
    )
    warnings = tuple(
        checks.loc[checks["status"] == "warn", "details"].astype(str)
    )
    if overall_status == "fail":
        action = "Stop promotion and investigate blocking staging failures."
    elif overall_status == "warn":
        action = "Hold artifact promotion pending warning review and real trial evidence."
    else:
        action = "Artifact may proceed to the next controlled staging review."
    return OperationalHealthSummary(
        overall_status=overall_status,
        pass_count=int(counts.get("pass", 0)),
        warn_count=int(counts.get("warn", 0)),
        fail_count=int(counts.get("fail", 0)),
        checks=checks,
        blocking_issues=blocking_issues,
        non_blocking_warnings=warnings,
        recommended_action=action,
    )
