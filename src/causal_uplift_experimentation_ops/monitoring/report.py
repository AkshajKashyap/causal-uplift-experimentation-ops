"""Generate the offline staging observability and promotion-gate report."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.artifacts.manifest import load_manifest
from causal_uplift_experimentation_ops.artifacts.policy_card import load_policy_config
from causal_uplift_experimentation_ops.monitoring.audit import (
    DEFAULT_AUDIT_PATH,
    AuditLogSummary,
    analyze_audit_log,
)
from causal_uplift_experimentation_ops.monitoring.drift import (
    PredictionDriftResult,
    check_input_drift,
    summarize_prediction_drift,
    worst_severity,
)
from causal_uplift_experimentation_ops.monitoring.health import (
    OperationalHealthSummary,
    build_operational_health,
)
from causal_uplift_experimentation_ops.monitoring.promotion import (
    PromotionDecision,
    evaluate_promotion,
)

DEFAULT_REFERENCE_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_ARTIFACT_PATH = Path("artifacts/policy_bundle")
DEFAULT_SCORES_PATH = DEFAULT_ARTIFACT_PATH / "batch_scores.csv"
DEFAULT_REPORT_PATH = Path("reports/staging_observability_report.md")
DEFAULT_POLICY_CARD_PATH = Path("reports/policy_card.md")
DEFAULT_PREREGISTRATION_PATH = Path("reports/experiment_preregistration.md")
DEFAULT_TRIAL_REPORT_PATH = Path("reports/prospective_policy_trial.md")


@dataclass(frozen=True)
class StagingObservabilityResult:
    """Monitoring results and the generated Markdown report path."""

    input_drift: pd.DataFrame
    input_drift_status: str
    prediction_drift: PredictionDriftResult
    audit_summary: AuditLogSummary
    health: OperationalHealthSummary
    promotion: PromotionDecision
    report_path: Path


def _format_value(value: object) -> str:
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return str(value)
        return f"{value:.6f}"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) or "None"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _markdown_table(data: pd.DataFrame) -> str:
    columns = [str(column) for column in data.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| "
        + " | ".join(_format_value(value) for value in row)
        + " |"
        for row in data.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def _prediction_missing_result(path: Path) -> PredictionDriftResult:
    metrics = pd.DataFrame.from_records(
        [
            {
                "metric_name": "scored_output_present",
                "reference_value": 1.0,
                "current_value": 0.0,
                "absolute_difference": 1.0,
                "severity": "fail",
                "notes": f"Batch scoring output is missing: {path}",
            }
        ]
    )
    return PredictionDriftResult(metrics=metrics, status="fail")


def _resolve_current_input(
    reference: pd.DataFrame,
    scores: pd.DataFrame | None,
    current_input_path: Path | str | None,
) -> tuple[pd.DataFrame, str]:
    if current_input_path is not None:
        path = Path(current_input_path)
        return pd.read_csv(path), str(path)
    if (
        scores is not None
        and "user_id" in scores
        and "user_id" in reference
    ):
        score_users = scores.loc[:, ["user_id"]].drop_duplicates()
        joined = score_users.merge(reference, on="user_id", how="left")
        return joined, "reference rows joined to batch scores by user_id"
    return reference.copy(), "reference dataset fallback"


def render_staging_observability_report(
    *,
    manifest: dict[str, object],
    config_model_name: str,
    config_policy_name: str,
    current_input_source: str,
    input_drift: pd.DataFrame,
    prediction_drift: PredictionDriftResult,
    audit_summary: AuditLogSummary,
    health: OperationalHealthSummary,
    promotion: PromotionDecision,
) -> str:
    """Render all monitoring checks and the deterministic promotion decision."""
    dataset = manifest.get("dataset_fingerprint", {})
    fingerprint = (
        dataset.get("fingerprint", "unknown")
        if isinstance(dataset, dict)
        else "unknown"
    )
    audit_metrics = pd.DataFrame(
        [
            {"metric": name, "value": value}
            for name, value in audit_summary.metrics.items()
        ]
    )
    endpoint_names = sorted(
        set(audit_summary.endpoint_request_counts)
        | set(audit_summary.endpoint_recommendation_counts)
    )
    endpoint_metrics = pd.DataFrame(
        [
            {
                "endpoint": endpoint,
                "requests": audit_summary.endpoint_request_counts.get(endpoint, 0),
                "recommendations": (
                    audit_summary.endpoint_recommendation_counts.get(endpoint, 0)
                ),
            }
            for endpoint in endpoint_names
        ],
        columns=["endpoint", "requests", "recommendations"],
    )
    if endpoint_metrics.empty:
        endpoint_metrics = pd.DataFrame(
            [{"endpoint": "None observed", "requests": 0, "recommendations": 0}]
        )
    blocking = list(health.blocking_issues)
    if promotion.decision != "promote":
        blocking.extend(promotion.reasons)
    blocking = list(dict.fromkeys(blocking))
    blocking_text = "\n".join(f"- {item}" for item in blocking) or "- None"
    warning_text = (
        "\n".join(f"- {item}" for item in health.non_blocking_warnings)
        or "- None"
    )
    reason_text = "\n".join(f"- {item}" for item in promotion.reasons)

    return f"""# Staging Observability Report

## Scope and identity

- Artifact version: **{manifest.get("artifact_version", "unknown")}**
- Model: **{config_model_name}**
- Policy: **{config_policy_name}**
- Dataset fingerprint: `{fingerprint}`
- Current raw-input source: `{current_input_source}`

This report provides deterministic offline/staging monitoring. It is not continuous production
observability and does not grant production approval.

## Input drift

- Status: **{worst_severity(input_drift["severity"])}**

{_markdown_table(input_drift)}

## Prediction drift

- Status: **{prediction_drift.status}**

{_markdown_table(prediction_drift.metrics)}

## API audit log

- Status: **{audit_summary.status}**

{_markdown_table(audit_metrics)}

### Endpoint activity

{_markdown_table(endpoint_metrics)}

## Operational health

- Overall status: **{health.overall_status}**
- Pass checks: {health.pass_count}
- Warning checks: {health.warn_count}
- Failed checks: {health.fail_count}

{_markdown_table(health.checks)}

## Promotion gate

- Decision: **{promotion.decision}**
- Recommended next action: {promotion.recommended_action}

Reasons:

{reason_text}

### Blocking issues

{blocking_text}

### Non-blocking warnings

{warning_text}

## Limitation

These checks inspect local CSV/JSONL snapshots and static reports. They do not provide durable
telemetry, alerting, tracing, data freshness enforcement, or a production SLO. All evaluation
evidence remains synthetic, so a real pre-registered randomized trial is still required before
production treatment delivery.
"""


def generate_staging_observability_report(
    *,
    reference_path: Path | str = DEFAULT_REFERENCE_PATH,
    current_input_path: Path | str | None = None,
    scores_path: Path | str = DEFAULT_SCORES_PATH,
    reference_scores_path: Path | str | None = None,
    audit_path: Path | str = DEFAULT_AUDIT_PATH,
    artifact_path: Path | str = DEFAULT_ARTIFACT_PATH,
    policy_card_path: Path | str = DEFAULT_POLICY_CARD_PATH,
    preregistration_path: Path | str = DEFAULT_PREREGISTRATION_PATH,
    prospective_trial_path: Path | str = DEFAULT_TRIAL_REPORT_PATH,
    output_path: Path | str = DEFAULT_REPORT_PATH,
    accept_simulated_trial: bool = False,
) -> StagingObservabilityResult:
    """Run snapshot monitoring and write a staging promotion report."""
    manifest = load_manifest(artifact_path)
    config = load_policy_config(artifact_path)
    reference = pd.read_csv(reference_path)
    score_file = Path(scores_path)
    scores = pd.read_csv(score_file) if score_file.exists() else None
    current, current_source = _resolve_current_input(
        reference,
        scores,
        current_input_path,
    )
    features = tuple(str(item) for item in manifest.get("feature_columns", ()))
    if not features:
        raise ValueError("Artifact manifest has no feature_columns")
    input_drift = check_input_drift(reference, current, features)

    if scores is None:
        prediction_drift = _prediction_missing_result(score_file)
    else:
        reference_scores = (
            pd.read_csv(reference_scores_path)
            if reference_scores_path is not None
            else scores
        )
        prediction_drift = summarize_prediction_drift(
            scores,
            reference_scores,
            treatment_cost_per_user=config.treatment_cost_per_user,
        )
    audit_summary = analyze_audit_log(audit_path)
    health = build_operational_health(
        input_drift,
        prediction_drift,
        audit_summary,
        artifact_directory=artifact_path,
        policy_card_path=policy_card_path,
        preregistration_path=preregistration_path,
        prospective_trial_path=prospective_trial_path,
    )
    promotion = evaluate_promotion(
        health,
        synthetic_only=True,
        accept_simulated_trial=accept_simulated_trial,
    )
    content = render_staging_observability_report(
        manifest=manifest,
        config_model_name=config.model_name,
        config_policy_name=config.policy_name,
        current_input_source=current_source,
        input_drift=input_drift,
        prediction_drift=prediction_drift,
        audit_summary=audit_summary,
        health=health,
        promotion=promotion,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return StagingObservabilityResult(
        input_drift=input_drift,
        input_drift_status=worst_severity(input_drift["severity"]),
        prediction_drift=prediction_drift,
        audit_summary=audit_summary,
        health=health,
        promotion=promotion,
        report_path=destination,
    )


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE_PATH)
    parser.add_argument("--current-input", type=Path)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES_PATH)
    parser.add_argument("--reference-scores", type=Path)
    parser.add_argument("--audit-log", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--policy-card", type=Path, default=DEFAULT_POLICY_CARD_PATH)
    parser.add_argument(
        "--preregistration",
        type=Path,
        default=DEFAULT_PREREGISTRATION_PATH,
    )
    parser.add_argument(
        "--prospective-trial",
        type=Path,
        default=DEFAULT_TRIAL_REPORT_PATH,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--accept-simulated-trial", action="store_true")
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate the staging observability report."""
    options = _parse_args(args)
    result = generate_staging_observability_report(
        reference_path=options.reference,
        current_input_path=options.current_input,
        scores_path=options.scores,
        reference_scores_path=options.reference_scores,
        audit_path=options.audit_log,
        artifact_path=options.bundle,
        policy_card_path=options.policy_card,
        preregistration_path=options.preregistration,
        prospective_trial_path=options.prospective_trial,
        output_path=options.output,
        accept_simulated_trial=options.accept_simulated_trial,
    )
    print(f"Wrote staging observability report to {result.report_path}")
    print(
        "Statuses: "
        f"input={result.input_drift_status}, "
        f"prediction={result.prediction_drift.status}, "
        f"audit={result.audit_summary.status}, "
        f"health={result.health.overall_status}"
    )
    print(f"Promotion decision: {result.promotion.decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
