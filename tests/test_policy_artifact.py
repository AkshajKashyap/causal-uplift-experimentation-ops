import pytest

from causal_uplift_experimentation_ops.artifacts import (
    PolicyDecisionConfig,
    fingerprint_config,
    fingerprint_dataset,
    generate_policy_artifact,
    load_policy_bundle,
    score_policy_batch,
)
from causal_uplift_experimentation_ops.data import generate_synthetic_experiment


@pytest.fixture(scope="module")
def artifact_result(tmp_path_factory: pytest.TempPathFactory):
    directory = tmp_path_factory.mktemp("policy_artifact")
    data = generate_synthetic_experiment(n_users=500, seed=313)
    result = generate_policy_artifact(
        data,
        artifact_directory=directory / "bundle",
        policy_card_path=directory / "policy_card.md",
        manifest_report_path=directory / "policy_artifact_manifest.md",
    )
    return data, result


def test_policy_config_validates_valid_fields() -> None:
    config = PolicyDecisionConfig()

    assert config.model_name == "logistic_s_learner"
    assert config.policy_name == "all_positive_uplift"


def test_empty_model_name_raises() -> None:
    with pytest.raises(ValueError, match="model_name must not be empty"):
        PolicyDecisionConfig(model_name="")


def test_empty_policy_name_raises() -> None:
    with pytest.raises(ValueError, match="policy_name must not be empty"):
        PolicyDecisionConfig(policy_name=" ")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("value_per_conversion", 0.0, "value_per_conversion must be positive"),
        (
            "treatment_cost_per_user",
            -1.0,
            "treatment_cost_per_user must be non-negative",
        ),
    ],
)
def test_invalid_value_assumptions_raise(
    field: str,
    value: float,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        PolicyDecisionConfig(**{field: value})


def test_dataset_fingerprint_is_deterministic() -> None:
    data = generate_synthetic_experiment(n_users=100, seed=17)

    assert fingerprint_dataset(data) == fingerprint_dataset(data.copy())


def test_config_fingerprint_is_deterministic() -> None:
    first = PolicyDecisionConfig(creation_timestamp="2026-01-01T00:00:00+00:00")
    second = PolicyDecisionConfig(creation_timestamp="2027-01-01T00:00:00+00:00")

    assert fingerprint_config(first) == fingerprint_config(second)


def test_policy_bundle_files_are_created(artifact_result) -> None:
    _, result = artifact_result
    expected = {
        "model.joblib",
        "policy_config.json",
        "manifest.json",
        "feature_columns.json",
        "value_assumptions.json",
        "README.md",
        "batch_scores.csv",
    }

    assert expected.issubset(
        {path.name for path in result.frozen_artifact.artifact_directory.iterdir()}
    )


def test_saved_model_bundle_can_be_loaded(artifact_result) -> None:
    _, result = artifact_result
    bundle = load_policy_bundle(result.frozen_artifact.artifact_directory)

    assert bundle.model.is_fitted
    assert bundle.config.artifact_version == "1.0.0"


def test_batch_scoring_creates_predicted_uplift(artifact_result) -> None:
    data, result = artifact_result
    scores = score_policy_batch(data, result.frozen_artifact.bundle)

    assert "predicted_uplift" in scores
    assert scores["predicted_uplift"].notna().all()


def test_batch_scoring_creates_recommended_treatment(artifact_result) -> None:
    data, result = artifact_result
    scores = score_policy_batch(data, result.frozen_artifact.bundle)

    assert "recommended_treatment" in scores
    assert set(scores["recommended_treatment"]).issubset({0, 1})


def test_batch_scoring_excludes_true_uplift_by_default(artifact_result) -> None:
    data, result = artifact_result
    scores = score_policy_batch(data, result.frozen_artifact.bundle)

    assert "true_uplift" not in scores
    assert "synthetic_debug_true_uplift" not in scores


def test_missing_required_feature_raises(artifact_result) -> None:
    data, result = artifact_result

    with pytest.raises(ValueError, match="Missing feature columns: age"):
        score_policy_batch(
            data.drop(columns="age"),
            result.frozen_artifact.bundle,
        )


def test_policy_card_report_is_created(artifact_result) -> None:
    _, result = artifact_result

    assert result.policy_card_path.exists()
    assert "# Policy Card" in result.policy_card_path.read_text(encoding="utf-8")


def test_manifest_report_is_created(artifact_result) -> None:
    _, result = artifact_result

    assert result.manifest_report_path.exists()
    assert "# Policy Artifact Manifest" in result.manifest_report_path.read_text(
        encoding="utf-8"
    )


def test_artifact_manifest_contains_expected_paths(artifact_result) -> None:
    _, result = artifact_result
    artifact_files = result.manifest["artifact_files"]

    assert isinstance(artifact_files, dict)
    assert {
        "model.joblib",
        "policy_config.json",
        "feature_columns.json",
        "value_assumptions.json",
        "README.md",
        "batch_scores.csv",
    }.issubset(artifact_files)
    assert result.manifest["config_fingerprint"]
    assert result.manifest["dataset_fingerprint"]["fingerprint"]
