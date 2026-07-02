from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.policy import (
    PolicyValueConfig,
    compare_model_policies,
    compare_policies,
    estimate_policy_value,
    generate_policy_report,
    oracle_policy,
    random_policy,
    target_positive_uplift,
    target_top_fraction,
    target_top_k,
)

EXPECTED_POLICIES = {
    "top_10_percent",
    "top_20_percent",
    "top_30_percent",
    "positive_uplift",
    "random_matched_20_percent",
    "oracle_matched_20_percent",
}
EXPECTED_MODELS = {
    "logistic_t_learner",
    "logistic_s_learner",
    "random_forest_t_learner",
    "random_baseline",
    "oracle_baseline",
}


@pytest.fixture(scope="module")
def scored_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": np.arange(1, 11),
            "treatment": [0, 1] * 5,
            "conversion": [0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
            "predicted_uplift": [0.10, 0.08, 0.06, 0.04, 0.02, 0.01, -0.01, -0.02, -0.03, -0.04],
            "true_uplift": [0.09, 0.07, 0.08, 0.03, 0.01, 0.02, 0.00, -0.01, -0.02, -0.03],
        }
    )


@pytest.fixture(scope="module")
def experiment_data() -> pd.DataFrame:
    return generate_synthetic_experiment(n_users=500, seed=515)


def test_top_fraction_selects_expected_count(scored_data: pd.DataFrame) -> None:
    selected = target_top_fraction(scored_data, 0.3)

    assert len(selected) == 3


def test_top_k_selects_expected_users(scored_data: pd.DataFrame) -> None:
    selected = target_top_k(scored_data, 2)

    assert selected["user_id"].tolist() == [1, 2]


def test_positive_policy_selects_only_positive_scores(scored_data: pd.DataFrame) -> None:
    selected = target_positive_uplift(scored_data)

    assert (selected["predicted_uplift"] > 0).all()
    assert len(selected) == 6


def test_random_policy_is_deterministic(scored_data: pd.DataFrame) -> None:
    first = random_policy(scored_data, 4, seed=7)
    second = random_policy(scored_data, 4, seed=7)

    pd.testing.assert_frame_equal(first, second)


def test_oracle_policy_requires_true_uplift(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Oracle policy requires 'true_uplift'"):
        oracle_policy(scored_data.drop(columns="true_uplift"), 2)


def test_budget_limits_selected_users(scored_data: pd.DataFrame) -> None:
    config = PolicyValueConfig(treatment_cost_per_user=2.0, budget=5.0)

    assert len(target_top_fraction(scored_data, 1.0, config)) == 2


def test_capacity_limits_selected_users(scored_data: pd.DataFrame) -> None:
    config = PolicyValueConfig(capacity_fraction=0.2)

    assert len(target_top_fraction(scored_data, 1.0, config)) == 2


def test_treatment_cost_reduces_net_value(scored_data: pd.DataFrame) -> None:
    selected = target_top_k(scored_data, 6)
    low_cost = estimate_policy_value(
        selected,
        len(scored_data),
        PolicyValueConfig(treatment_cost_per_user=1.0),
        "test",
    )
    high_cost = estimate_policy_value(
        selected,
        len(scored_data),
        PolicyValueConfig(treatment_cost_per_user=5.0),
        "test",
    )

    assert high_cost.net_value < low_cost.net_value


def test_roi_is_finite_with_positive_cost(scored_data: pd.DataFrame) -> None:
    outcome = estimate_policy_value(
        target_top_k(scored_data, 6),
        len(scored_data),
        PolicyValueConfig(treatment_cost_per_user=1.0),
        "test",
    )

    assert np.isfinite(outcome.roi)


def test_policy_comparison_returns_expected_names(scored_data: pd.DataFrame) -> None:
    comparison = compare_policies(scored_data)

    assert set(comparison["policy_name"]) == EXPECTED_POLICIES


def test_model_policy_comparison_returns_expected_models(
    experiment_data: pd.DataFrame,
) -> None:
    result = compare_model_policies(experiment_data, n_splits=3, seed=4)

    assert set(result.comparison["model"]) == EXPECTED_MODELS


def test_policy_report_generation(
    experiment_data: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report_path = generate_policy_report(
        experiment_data,
        tmp_path / "targeting_policy_simulation.md",
        n_splits=3,
    )

    assert report_path.exists()
    assert "# Targeting Policy Simulation" in report_path.read_text(encoding="utf-8")


def test_invalid_fraction_raises_clear_error(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="fraction must be between 0 and 1"):
        target_top_fraction(scored_data, 1.2)


def test_missing_predicted_uplift_raises_clear_error(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Missing policy columns: predicted_uplift"):
        target_top_fraction(scored_data.drop(columns="predicted_uplift"), 0.2)
