from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.policy import (
    PolicyValueConfig,
    analyze_policy_uncertainty,
    bootstrap_policy_values,
    generate_uncertainty_report,
    summarize_policy_bootstrap,
)


@pytest.fixture(scope="module")
def scored_data() -> pd.DataFrame:
    rows = 200
    return pd.DataFrame(
        {
            "user_id": np.arange(1, rows + 1),
            "treatment": np.arange(rows) % 2,
            "conversion": ((np.arange(rows) % 7) < (2 + np.arange(rows) % 2)).astype(int),
            "predicted_uplift": np.linspace(0.12, -0.04, rows),
            "true_uplift": np.linspace(0.10, -0.02, rows),
        }
    )


@pytest.fixture(scope="module")
def bootstrap_results(scored_data: pd.DataFrame) -> pd.DataFrame:
    return bootstrap_policy_values(scored_data, n_bootstrap=6, seed=3)


@pytest.fixture(scope="module")
def uncertainty_result():
    data = generate_synthetic_experiment(n_users=400, seed=818)
    return analyze_policy_uncertainty(data, n_splits=2, n_bootstrap=4, seed=5)


def test_bootstrap_returns_every_sample_and_policy(
    bootstrap_results: pd.DataFrame,
) -> None:
    assert bootstrap_results["bootstrap_id"].nunique() == 6
    assert (bootstrap_results.groupby("bootstrap_id")["policy_name"].nunique() == 6).all()


def test_policy_bootstrap_is_deterministic(scored_data: pd.DataFrame) -> None:
    first = bootstrap_policy_values(scored_data, n_bootstrap=4, seed=12)
    second = bootstrap_policy_values(scored_data, n_bootstrap=4, seed=12)

    pd.testing.assert_frame_equal(first, second)


def test_interval_summary_has_percentile_columns(
    bootstrap_results: pd.DataFrame,
) -> None:
    summary = summarize_policy_bootstrap(bootstrap_results)

    assert {"net_value_2_5", "net_value_50", "net_value_97_5"}.issubset(
        summary.columns
    )


def test_positive_net_probability_is_valid(bootstrap_results: pd.DataFrame) -> None:
    summary = summarize_policy_bootstrap(bootstrap_results)

    assert summary["probability_positive_net_value"].between(0, 1).all()


def test_beats_random_probability_is_valid_where_available(
    bootstrap_results: pd.DataFrame,
) -> None:
    summary = summarize_policy_bootstrap(bootstrap_results)
    available = summary["probability_beats_random"].dropna()

    assert available.between(0, 1).all()


def test_full_population_policy_excludes_trivial_random_comparison(
    scored_data: pd.DataFrame,
) -> None:
    all_positive = scored_data.assign(predicted_uplift=0.1)
    results = bootstrap_policy_values(all_positive, n_bootstrap=3)
    positive_policy = results[results["policy_name"] == "positive_uplift"]

    assert positive_policy["beats_random"].isna().all()


def test_oracle_regret_columns_exist(bootstrap_results: pd.DataFrame) -> None:
    summary = summarize_policy_bootstrap(bootstrap_results)

    assert {
        "mean_oracle_regret",
        "median_oracle_regret",
        "oracle_regret_2_5",
        "oracle_regret_97_5",
    }.issubset(summary.columns)


def test_missing_true_uplift_excludes_oracle_values(scored_data: pd.DataFrame) -> None:
    results = bootstrap_policy_values(
        scored_data.drop(columns="true_uplift"),
        n_bootstrap=3,
    )
    summary = summarize_policy_bootstrap(results)

    assert "oracle_matched_20_percent" not in set(summary["policy_name"])
    assert summary["mean_oracle_regret"].isna().all()


def test_chosen_policy_appears_in_summary(uncertainty_result) -> None:
    assert "logistic_s_learner__positive_uplift" in set(
        uncertainty_result.summary["policy_id"]
    )


def test_random_baseline_appears_in_summary(uncertainty_result) -> None:
    assert "random_baseline" in set(uncertainty_result.summary["model"])


def test_nonpositive_bootstrap_count_raises(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="n_bootstrap must be greater than 0"):
        bootstrap_policy_values(scored_data, n_bootstrap=0)


def test_missing_predicted_uplift_raises(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Missing policy columns: predicted_uplift"):
        bootstrap_policy_values(
            scored_data.drop(columns="predicted_uplift"),
            n_bootstrap=2,
        )


def test_negative_treatment_cost_raises() -> None:
    with pytest.raises(ValueError, match="treatment_cost_per_user must be non-negative"):
        PolicyValueConfig(treatment_cost_per_user=-1.0)


def test_nonpositive_conversion_value_raises(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="value_per_conversion must be greater than 0"):
        bootstrap_policy_values(
            scored_data,
            config=PolicyValueConfig(value_per_conversion=0.0),
            n_bootstrap=2,
        )


def test_uncertainty_report_generation(tmp_path: Path) -> None:
    data = generate_synthetic_experiment(n_users=400, seed=616)
    report_path = generate_uncertainty_report(
        data,
        tmp_path / "policy_value_uncertainty.md",
        n_splits=2,
        n_bootstrap=3,
    )

    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# Policy Value Bootstrap Uncertainty" in report
    assert "nan%" not in report
