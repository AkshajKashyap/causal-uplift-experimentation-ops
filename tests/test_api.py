from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from causal_uplift_experimentation_ops.api.app import app, create_app
from causal_uplift_experimentation_ops.api.errors import ArtifactLoadError
from causal_uplift_experimentation_ops.api.report import generate_api_report
from causal_uplift_experimentation_ops.api.service import PolicyInferenceService
from causal_uplift_experimentation_ops.artifacts import generate_policy_artifact
from causal_uplift_experimentation_ops.data import generate_synthetic_experiment

VALID_USER = {
    "user_id": 9001,
    "age": 35,
    "prior_purchases": 4,
    "avg_order_value": 82.5,
    "days_since_last_purchase": 21,
    "channel": "email",
}


@pytest.fixture(scope="module")
def artifact_directory(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("api_artifact")
    data = generate_synthetic_experiment(n_users=500, seed=414)
    result = generate_policy_artifact(
        data,
        artifact_directory=directory / "bundle",
        policy_card_path=directory / "policy_card.md",
        manifest_report_path=directory / "manifest.md",
    )
    return result.frozen_artifact.artifact_directory


@pytest.fixture(scope="module")
def client(artifact_directory: Path):
    with TestClient(create_app(artifact_directory)) as test_client:
        yield test_client


def test_api_app_imports_successfully() -> None:
    assert app.title == "Causal Uplift Policy Staging API"


def test_health_returns_ready_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["artifact_loaded"] is True
    assert response.json()["status"] == "ok"


def test_version_returns_artifact_metadata(client: TestClient) -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json()["artifact_version"] == "1.0.0"
    assert response.json()["dataset_fingerprint"]
    assert response.json()["config_fingerprint"]


def test_policy_returns_selected_features(client: TestClient) -> None:
    response = client.get("/policy")

    assert response.status_code == 200
    assert response.json()["selected_feature_columns"] == [
        "age",
        "prior_purchases",
        "avg_order_value",
        "days_since_last_purchase",
        "channel",
    ]


def test_score_returns_uplift_and_recommendation(client: TestClient) -> None:
    response = client.post("/score", json=VALID_USER)

    assert response.status_code == 200
    assert isinstance(response.json()["predicted_uplift"], float)
    assert response.json()["recommended_treatment"] in {0, 1}
    assert response.json()["reason"] == "predicted_uplift > 0"


def test_score_does_not_require_outcomes(client: TestClient) -> None:
    response = client.post("/score", json=VALID_USER)

    assert response.status_code == 200
    assert {"conversion", "spend", "true_uplift", "treatment"}.isdisjoint(
        VALID_USER
    )


def test_batch_returns_one_score_per_user(client: TestClient) -> None:
    second_user = {**VALID_USER, "user_id": 9002, "channel": "organic"}
    response = client.post(
        "/score-batch",
        json={"users": [VALID_USER, second_user]},
    )

    assert response.status_code == 200
    assert response.json()["batch_size"] == 2
    assert len(response.json()["scores"]) == 2


def test_empty_batch_returns_clear_400(client: TestClient) -> None:
    response = client.post("/score-batch", json={"users": []})

    assert response.status_code == 400
    assert "at least one user" in response.json()["detail"]


def test_oversized_batch_returns_clear_400(client: TestClient) -> None:
    response = client.post(
        "/score-batch",
        json={"users": [VALID_USER] * 1_001},
    )

    assert response.status_code == 400
    assert "maximum size of 1000" in response.json()["detail"]


def test_invalid_payload_returns_validation_error(client: TestClient) -> None:
    response = client.post("/score", json={**VALID_USER, "age": "thirty"})

    assert response.status_code == 422


def test_api_response_excludes_true_uplift(client: TestClient) -> None:
    response = client.post("/score", json=VALID_USER)

    assert response.status_code == 200
    assert "true_uplift" not in response.json()


def test_manifest_returns_safe_metadata(client: TestClient) -> None:
    response = client.get("/manifest")

    assert response.status_code == 200
    assert "artifact_files" in response.json()
    assert "model.joblib" in response.json()["artifact_files"]
    assert "content_sha256" not in response.json()


def test_service_loading_missing_bundle_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ArtifactLoadError, match="missing required files"):
        PolicyInferenceService(tmp_path / "missing")


def test_api_report_is_created(
    artifact_directory: Path,
    tmp_path: Path,
) -> None:
    report_path = generate_api_report(
        artifact_directory,
        tmp_path / "api_staging_service.md",
    )

    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# FastAPI Staging Policy Service" in report
    assert "not production" in report.lower()
