from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.evaluation.comparison import score_comparison_models
from causal_uplift_experimentation_ops.policy import (
    PolicyValueConfig,
    break_even_analysis,
    compare_scored_model_policies,
    generate_sensitivity_report,
    one_way_sensitivity,
    summarize_decision_stability,
    two_way_sensitivity_grid,
)

REQUIRED_STABILITY_FIELDS = {
    "most_frequent_best_model",
    "most_frequent_best_policy",
    "same_model_win_rate",
    "same_policy_win_rate",
    "learned_beats_random_rate",
    "positive_learned_net_value_rate",
    "average_learned_oracle_ratio",
    "worst_case_learned_net_value",
    "worst_case_roi",
    "best_case_learned_net_value",
    "best_case_roi",
}


@pytest.fixture(scope="module")
def experiment_data() -> pd.DataFrame:
    return generate_synthetic_experiment(n_users=500, seed=909)


@pytest.fixture(scope="module")
def scored_predictions(experiment_data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    predictions, _ = score_comparison_models(experiment_data, n_splits=3, seed=6)
    return predictions


@pytest.fixture(scope="module")
def cost_sensitivity(scored_predictions) -> pd.DataFrame:
    return one_way_sensitivity(
        scored_predictions,
        "treatment_cost_per_user",
        [0.5, 1.0, 2.0],
    )


def test_one_way_returns_every_requested_value(scored_predictions) -> None:
    result = one_way_sensitivity(
        scored_predictions,
        "value_per_conversion",
        [25.0, 50.0, 100.0],
    )

    assert result["assumption_value"].tolist() == [25.0, 50.0, 100.0]


def test_two_way_grid_has_expected_rows(scored_predictions) -> None:
    result = two_way_sensitivity_grid(
        scored_predictions,
        "value_per_conversion",
        [50.0, 100.0],
        "treatment_cost_per_user",
        [0.5, 1.0, 2.0],
    )

    assert len(result) == 6


def test_stability_summary_has_required_fields(cost_sensitivity: pd.DataFrame) -> None:
    summary = summarize_decision_stability(cost_sensitivity)

    assert REQUIRED_STABILITY_FIELDS.issubset(summary.to_dict())


def test_break_even_values_are_finite(scored_predictions) -> None:
    comparison = compare_scored_model_policies(
        scored_predictions,
        PolicyValueConfig(),
    )
    result = break_even_analysis(comparison)

    assert np.isfinite(result.maximum_treatment_cost)
    assert np.isfinite(result.minimum_value_per_conversion)


def test_rising_cost_does_not_improve_best_net(cost_sensitivity: pd.DataFrame) -> None:
    ordered = cost_sensitivity.sort_values("assumption_value")

    assert ordered["best_net_value"].is_monotonic_decreasing


def test_higher_conversion_value_does_not_reduce_gross_value(scored_predictions) -> None:
    result = one_way_sensitivity(
        scored_predictions,
        "value_per_conversion",
        [25.0, 50.0, 100.0],
    ).sort_values("assumption_value")

    assert result["best_net_gross_value"].is_monotonic_increasing


def test_budget_constraint_is_respected(scored_predictions) -> None:
    result = one_way_sensitivity(scored_predictions, "budget", [50.0])

    assert result.loc[0, "best_net_selected_users"] <= 50


def test_capacity_constraint_is_respected(scored_predictions) -> None:
    result = one_way_sensitivity(scored_predictions, "capacity_fraction", [0.1])

    assert result.loc[0, "best_net_selected_users"] <= 50


def test_learned_random_comparison_columns_exist(cost_sensitivity: pd.DataFrame) -> None:
    assert {"random_net_value", "learned_random_net_difference"}.issubset(
        cost_sensitivity.columns
    )


def test_oracle_comparison_columns_exist(cost_sensitivity: pd.DataFrame) -> None:
    assert {"oracle_net_value", "learned_oracle_net_ratio"}.issubset(
        cost_sensitivity.columns
    )


def test_missing_predicted_uplift_raises(scored_predictions) -> None:
    invalid = {
        name: frame.drop(columns="predicted_uplift")
        for name, frame in scored_predictions.items()
    }

    with pytest.raises(ValueError, match="Missing policy columns: predicted_uplift"):
        one_way_sensitivity(invalid, "budget", [100.0])


def test_negative_treatment_cost_raises(scored_predictions) -> None:
    with pytest.raises(ValueError, match="treatment_cost_per_user must be non-negative"):
        one_way_sensitivity(
            scored_predictions,
            "treatment_cost_per_user",
            [-1.0],
        )


def test_nonpositive_conversion_value_raises(scored_predictions) -> None:
    with pytest.raises(ValueError, match="value_per_conversion must be greater than 0"):
        one_way_sensitivity(
            scored_predictions,
            "value_per_conversion",
            [0.0],
        )


def test_sensitivity_report_generation(
    experiment_data: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report_path = generate_sensitivity_report(
        experiment_data,
        tmp_path / "policy_sensitivity_analysis.md",
        n_splits=3,
    )

    assert report_path.exists()
    assert "# Policy Sensitivity Analysis" in report_path.read_text(encoding="utf-8")
