import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from causal_uplift_experimentation_ops.api.app import create_app
from causal_uplift_experimentation_ops.api.safety import StagingAPIConfig
from causal_uplift_experimentation_ops.artifacts import generate_policy_artifact
from causal_uplift_experimentation_ops.data import generate_synthetic_experiment

VALID_USER = {
    "user_id": 30001,
    "age": 35,
    "prior_purchases": 4,
    "avg_order_value": 82.5,
    "days_since_last_purchase": 21,
    "channel": "email",
}


@pytest.fixture(scope="module")
def artifact_directory(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("api_safety_artifact")
    data = generate_synthetic_experiment(n_users=500, seed=515)
    result = generate_policy_artifact(
        data,
        artifact_directory=directory / "bundle",
        policy_card_path=directory / "policy_card.md",
        manifest_report_path=directory / "manifest.md",
    )
    return result.frozen_artifact.artifact_directory


def _users(count: int) -> list[dict[str, object]]:
    return [
        {
            **VALID_USER,
            "user_id": int(VALID_USER["user_id"]) + index,
            "prior_purchases": index + 1,
        }
        for index in range(count)
    ]


def test_health_works_without_api_key(artifact_directory: Path) -> None:
    config = StagingAPIConfig(
        require_api_key=True,
        api_key_env_var="TEST_POLICY_API_KEY",
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_protected_endpoint_rejects_missing_key(
    artifact_directory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_POLICY_API_KEY", "secret")
    config = StagingAPIConfig(
        require_api_key=True,
        api_key_env_var="TEST_POLICY_API_KEY",
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.post("/score", json=VALID_USER)

    assert response.status_code == 401
    assert response.json()["error_type"] == "authentication_error"


def test_protected_endpoint_rejects_invalid_key(
    artifact_directory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_POLICY_API_KEY", "secret")
    config = StagingAPIConfig(
        require_api_key=True,
        api_key_env_var="TEST_POLICY_API_KEY",
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.get("/policy", headers={"X-API-Key": "wrong"})

    assert response.status_code == 401


def test_protected_endpoint_accepts_valid_key(
    artifact_directory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_POLICY_API_KEY", "secret")
    config = StagingAPIConfig(
        require_api_key=True,
        api_key_env_var="TEST_POLICY_API_KEY",
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.get("/policy", headers={"X-API-Key": "secret"})

    assert response.status_code == 200


def test_score_includes_request_id(artifact_directory: Path) -> None:
    with TestClient(create_app(artifact_directory)) as client:
        response = client.post("/score", json=VALID_USER)

    assert response.status_code == 200
    assert response.json()["request_id"]
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


def test_batch_includes_one_request_id(artifact_directory: Path) -> None:
    with TestClient(create_app(artifact_directory)) as client:
        response = client.post("/score-batch", json={"users": _users(3)})

    request_id = response.json()["request_id"]
    assert request_id
    assert {
        score["request_id"] for score in response.json()["scores"]
    } == {request_id}


def test_audit_log_is_feature_free(
    artifact_directory: Path,
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "audit.jsonl"
    config = StagingAPIConfig(
        enable_audit_log=True,
        audit_log_path=audit_path,
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.post("/score", json=VALID_USER)

    assert response.status_code == 200
    event = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
    assert event["endpoint"] == "/score"
    assert event["batch_size"] == 1
    assert event["recommended_treatment_count"] in {0, 1}
    forbidden = {
        "user_id",
        "age",
        "channel",
        "true_uplift",
        "conversion",
        "spend",
        "treatment",
        "api_key",
    }
    assert forbidden.isdisjoint(event)


def test_max_recommendations_suppresses_lower_uplift(
    artifact_directory: Path,
) -> None:
    config = StagingAPIConfig(
        max_recommendations_per_run=None,
        max_treatment_cost_per_run=None,
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.post(
            "/score-batch",
            json={"users": _users(3), "max_recommendations": 1},
        )

    result = response.json()
    recommended = [
        score for score in result["scores"] if score["recommended_treatment"]
    ]
    assert result["original_recommended_count"] == 3
    assert result["final_recommended_count"] == 1
    assert result["recommendations_suppressed_by_budget"] == 2
    assert recommended[0]["predicted_uplift"] == max(
        score["predicted_uplift"] for score in result["scores"]
    )


def test_max_treatment_cost_suppresses_recommendations(
    artifact_directory: Path,
) -> None:
    config = StagingAPIConfig(
        max_recommendations_per_run=None,
        max_treatment_cost_per_run=None,
    )
    with TestClient(create_app(artifact_directory, safety_config=config)) as client:
        response = client.post(
            "/score-batch",
            json={
                "users": _users(3),
                "max_treatment_cost": 2.0,
                "treatment_cost_per_user": 2.0,
            },
        )

    assert response.json()["final_recommended_count"] == 1
    assert response.json()["estimated_treatment_cost"] == 2.0
    assert response.json()["guardrail_applied"] is True


def test_metrics_increment_after_score_requests(
    artifact_directory: Path,
) -> None:
    with TestClient(create_app(artifact_directory)) as client:
        before = client.get("/metrics").json()
        client.post("/score", json=VALID_USER)
        client.post("/score-batch", json={"users": _users(2)})
        after = client.get("/metrics").json()

    assert after["total_score_requests"] == before["total_score_requests"] + 1
    assert after["total_batch_requests"] == before["total_batch_requests"] + 1
    assert after["total_users_scored"] == before["total_users_scored"] + 3


def test_empty_batch_still_returns_clear_error(
    artifact_directory: Path,
) -> None:
    with TestClient(create_app(artifact_directory)) as client:
        response = client.post("/score-batch", json={"users": []})

    assert response.status_code == 400
    assert response.json()["request_id"]


def test_oversized_batch_still_returns_clear_error(
    artifact_directory: Path,
) -> None:
    with TestClient(create_app(artifact_directory, max_batch_size=2)) as client:
        response = client.post("/score-batch", json={"users": _users(3)})

    assert response.status_code == 400
    assert "maximum size of 2" in response.json()["detail"]


def test_invalid_budget_guardrail_returns_clear_error(
    artifact_directory: Path,
) -> None:
    with TestClient(create_app(artifact_directory)) as client:
        response = client.post(
            "/score-batch",
            json={"users": _users(2), "max_treatment_cost": -1},
        )

    assert response.status_code == 422
    assert response.json()["error_type"] == "payload_validation_error"
    assert response.json()["request_id"]
