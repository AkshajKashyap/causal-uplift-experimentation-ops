import json
from pathlib import Path

import pandas as pd
import pytest

from causal_uplift_experimentation_ops.artifacts import generate_policy_artifact
from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.monitoring import (
    OperationalHealthSummary,
    analyze_audit_log,
    build_operational_health,
    check_input_drift,
    evaluate_promotion,
    generate_audit_smoke_log,
    summarize_prediction_drift,
)
from causal_uplift_experimentation_ops.monitoring.report import (
    generate_staging_observability_report,
)


@pytest.fixture(scope="module")
def monitoring_artifact(tmp_path_factory: pytest.TempPathFactory):
    directory = tmp_path_factory.mktemp("monitoring_artifact")
    data = generate_synthetic_experiment(n_users=400, seed=616)
    reference_path = directory / "reference.csv"
    data.to_csv(reference_path, index=False)
    result = generate_policy_artifact(
        data,
        artifact_directory=directory / "bundle",
        policy_card_path=directory / "policy_card.md",
        manifest_report_path=directory / "manifest_report.md",
    )
    preregistration_path = directory / "preregistration.md"
    preregistration_path.write_text("# Experiment pre-registration\n", encoding="utf-8")
    trial_path = directory / "trial.md"
    trial_path.write_text(
        "# Trial\n\n"
        "## Final randomized trial estimates\n\n"
        "| Guardrail | Status |\n"
        "| --- | --- |\n"
        "| Conversion | PASS |\n\n"
        "## MDE and power planning\n",
        encoding="utf-8",
    )
    return {
        "directory": directory,
        "data": data,
        "reference_path": reference_path,
        "result": result,
        "preregistration_path": preregistration_path,
        "trial_path": trial_path,
    }


def _scored_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "predicted_uplift": [-0.02, 0.01, 0.04, 0.08],
            "policy_eligible": [0, 1, 1, 1],
            "recommended_treatment": [0, 1, 1, 0],
        }
    )


def _promotion_health(statuses: dict[str, str]) -> OperationalHealthSummary:
    checks = pd.DataFrame(
        [
            {
                "check": name,
                "status": status,
                "details": f"{name} is {status}",
                "blocking": status == "fail",
            }
            for name, status in statuses.items()
        ]
    )
    counts = checks["status"].value_counts()
    overall = (
        "fail"
        if counts.get("fail", 0)
        else "warn"
        if counts.get("warn", 0)
        else "pass"
    )
    return OperationalHealthSummary(
        overall_status=overall,
        pass_count=int(counts.get("pass", 0)),
        warn_count=int(counts.get("warn", 0)),
        fail_count=int(counts.get("fail", 0)),
        checks=checks,
        blocking_issues=tuple(
            checks.loc[checks["status"] == "fail", "details"].astype(str)
        ),
        non_blocking_warnings=tuple(
            checks.loc[checks["status"] == "warn", "details"].astype(str)
        ),
        recommended_action="Review staging evidence.",
    )


def test_input_drift_returns_numeric_feature_rows() -> None:
    reference = pd.DataFrame({"age": [20, 30, 40, 50]})
    current = pd.DataFrame({"age": [21, 31, 41, 51]})

    result = check_input_drift(reference, current, ["age"])

    assert not result.loc[result["feature_type"] == "numeric"].empty
    assert "mean" in set(result["metric_name"])


def test_input_drift_returns_categorical_feature_rows() -> None:
    reference = pd.DataFrame({"channel": ["email", "social", "email"]})
    current = pd.DataFrame({"channel": ["email", "email", "social"]})

    result = check_input_drift(reference, current, ["channel"])

    assert not result.loc[result["feature_type"] == "categorical"].empty
    assert "category_frequency:email" in set(result["metric_name"])


def test_input_drift_detects_unseen_category_rate() -> None:
    reference = pd.DataFrame({"channel": ["email", "social", "email", "social"]})
    current = pd.DataFrame({"channel": ["email", "affiliate", "email", "social"]})

    result = check_input_drift(reference, current, ["channel"])
    unseen = result.loc[result["metric_name"] == "unseen_category_rate"].iloc[0]

    assert unseen["current_value"] == pytest.approx(0.25)
    assert unseen["severity"] == "fail"


def test_prediction_drift_requires_predicted_uplift() -> None:
    scores = _scored_data().drop(columns="predicted_uplift")

    with pytest.raises(ValueError, match="predicted_uplift"):
        summarize_prediction_drift(scores)


def test_prediction_drift_computes_recommendation_rate() -> None:
    result = summarize_prediction_drift(_scored_data())
    recommendation = result.metrics.loc[
        result.metrics["metric_name"] == "recommendation_rate"
    ].iloc[0]

    assert recommendation["current_value"] == pytest.approx(0.5)


def test_audit_log_handles_missing_file(tmp_path: Path) -> None:
    result = analyze_audit_log(tmp_path / "missing.jsonl")

    assert result.status == "warn"
    assert result.metrics["total_events"] == 0
    assert result.warnings


def test_audit_summary_computes_counts_and_latency(tmp_path: Path) -> None:
    events = [
        {
            "endpoint": "/score",
            "batch_size": 1,
            "recommended_treatment_count": 1,
            "status": "success",
            "latency_ms": 10.0,
            "artifact_version": "1.0.0",
            "model_name": "model",
            "policy_name": "policy",
        },
        {
            "endpoint": "/score-batch",
            "batch_size": 4,
            "recommended_treatment_count": 2,
            "status": "success",
            "latency_ms": 30.0,
            "artifact_version": "1.0.0",
            "model_name": "model",
            "policy_name": "policy",
        },
    ]
    path = tmp_path / "audit.jsonl"
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )

    result = analyze_audit_log(path)

    assert result.metrics["total_events"] == 2
    assert result.metrics["total_users_scored"] == 5
    assert result.metrics["total_recommendations"] == 3
    assert result.endpoint_request_counts == {"/score": 1, "/score-batch": 1}
    assert result.metrics["mean_latency_ms"] == pytest.approx(20.0)
    assert result.metrics["p95_latency_ms"] == pytest.approx(29.0)
    assert result.metrics["max_latency_ms"] == pytest.approx(30.0)


def test_operational_health_returns_valid_status(
    monitoring_artifact,
    tmp_path: Path,
) -> None:
    artifact = monitoring_artifact
    input_drift = check_input_drift(
        artifact["data"],
        artifact["data"],
        ["age", "channel"],
    )
    prediction_drift = summarize_prediction_drift(_scored_data())
    audit_path = generate_audit_smoke_log(
        tmp_path / "audit.jsonl",
        artifact["result"].frozen_artifact.artifact_directory,
    )

    health = build_operational_health(
        input_drift,
        prediction_drift,
        analyze_audit_log(audit_path),
        artifact_directory=artifact["result"].frozen_artifact.artifact_directory,
        policy_card_path=artifact["result"].policy_card_path,
        preregistration_path=artifact["preregistration_path"],
        prospective_trial_path=artifact["trial_path"],
    )

    assert health.overall_status in {"pass", "warn", "fail"}
    assert health.pass_count + health.warn_count + health.fail_count == len(
        health.checks
    )


def test_promotion_holds_when_reports_are_missing() -> None:
    health = _promotion_health(
        {
            "input_drift": "pass",
            "prediction_drift": "pass",
            "audit_log": "pass",
            "artifact_manifest": "pass",
            "policy_card": "fail",
            "experiment_preregistration": "fail",
            "prospective_trial_report": "fail",
            "prospective_trial_guardrails": "fail",
        }
    )

    result = evaluate_promotion(
        health,
        synthetic_only=False,
        accept_simulated_trial=True,
    )

    assert result.decision == "hold"
    assert result.reasons


def test_promotion_holds_for_synthetic_only_evidence() -> None:
    health = _promotion_health(
        {
            "input_drift": "pass",
            "prediction_drift": "pass",
            "audit_log": "pass",
            "artifact_manifest": "pass",
            "policy_card": "pass",
            "experiment_preregistration": "pass",
            "prospective_trial_report": "pass",
        }
    )

    result = evaluate_promotion(health)

    assert result.decision == "hold"
    assert any("synthetic-only" in reason for reason in result.reasons)


def test_promotion_rolls_back_when_drift_fails() -> None:
    health = _promotion_health(
        {
            "input_drift": "fail",
            "prediction_drift": "pass",
            "audit_log": "pass",
            "artifact_manifest": "pass",
        }
    )

    result = evaluate_promotion(health)

    assert result.decision == "rollback"


def test_audit_smoke_log_is_created(monitoring_artifact, tmp_path: Path) -> None:
    output = generate_audit_smoke_log(
        tmp_path / "audit.jsonl",
        monitoring_artifact["result"].frozen_artifact.artifact_directory,
    )

    assert output.exists()
    events = output.read_text(encoding="utf-8").splitlines()
    assert len(events) == 6
    assert json.loads(events[0])["request_id"] == "smoke-request-001"


def test_staging_observability_report_is_created(
    monitoring_artifact,
    tmp_path: Path,
) -> None:
    artifact = monitoring_artifact
    audit_path = generate_audit_smoke_log(
        tmp_path / "audit.jsonl",
        artifact["result"].frozen_artifact.artifact_directory,
    )
    output = tmp_path / "staging_observability.md"

    result = generate_staging_observability_report(
        reference_path=artifact["reference_path"],
        scores_path=artifact["result"].batch_scores_path,
        audit_path=audit_path,
        artifact_path=artifact["result"].frozen_artifact.artifact_directory,
        policy_card_path=artifact["result"].policy_card_path,
        preregistration_path=artifact["preregistration_path"],
        prospective_trial_path=artifact["trial_path"],
        output_path=output,
    )

    assert result.report_path.exists()
    content = output.read_text(encoding="utf-8")
    assert "# Staging Observability Report" in content
    assert "Promotion gate" in content
