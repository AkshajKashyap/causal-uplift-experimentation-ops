from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.evaluation import (
    add_oracle_uplift_score,
    auuc_score,
    generate_uplift_evaluation_report,
    qini_coefficient,
    split_experiment_data,
    top_k_policy_summary,
    uplift_ranking_table,
)


@pytest.fixture(scope="module")
def experiment_data() -> pd.DataFrame:
    return generate_synthetic_experiment(n_users=1_000, seed=123)


def test_train_test_split_is_deterministic(experiment_data: pd.DataFrame) -> None:
    first = split_experiment_data(experiment_data, seed=9)
    second = split_experiment_data(experiment_data, seed=9)

    pd.testing.assert_frame_equal(first.train, second.train)
    pd.testing.assert_frame_equal(first.test, second.test)
    assert first.feature_columns == second.feature_columns


def test_both_treatment_groups_exist_in_each_split(experiment_data: pd.DataFrame) -> None:
    split = split_experiment_data(experiment_data, seed=4)

    assert set(split.train["treatment"]) == {0, 1}
    assert set(split.test["treatment"]) == {0, 1}


def test_outcomes_are_excluded_from_feature_columns(experiment_data: pd.DataFrame) -> None:
    split = split_experiment_data(experiment_data)

    assert set(split.outcome_columns).isdisjoint(split.feature_columns)
    assert {"user_id", "treatment", "true_uplift"}.isdisjoint(split.feature_columns)
    assert split.feature_columns == (
        "age",
        "prior_purchases",
        "avg_order_value",
        "days_since_last_purchase",
        "channel",
    )


def test_uplift_ranking_table_has_expected_bins(experiment_data: pd.DataFrame) -> None:
    scored = add_oracle_uplift_score(experiment_data)
    ranking = uplift_ranking_table(scored, n_bins=10)

    assert len(ranking) == 10
    assert ranking["uplift_bin"].tolist() == list(range(1, 11))
    assert ranking["row_count"].sum() == len(experiment_data)


def test_auuc_and_qini_are_finite(experiment_data: pd.DataFrame) -> None:
    scored = add_oracle_uplift_score(experiment_data)

    assert np.isfinite(auuc_score(scored))
    assert np.isfinite(qini_coefficient(scored))


def test_top_k_policy_summary_is_valid(experiment_data: pd.DataFrame) -> None:
    scored = add_oracle_uplift_score(experiment_data)
    summary = top_k_policy_summary(scored)

    assert summary["target_fraction"].tolist() == pytest.approx([0.1, 0.2, 0.3])
    assert (summary["targeted_count"] > 0).all()
    assert (summary["treated_count"] + summary["control_count"] == summary["targeted_count"]).all()
    assert np.isfinite(summary["estimated_uplift"]).all()


def test_report_generation_creates_markdown(
    experiment_data: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report_path = generate_uplift_evaluation_report(
        experiment_data,
        tmp_path / "uplift_evaluation.md",
    )

    assert report_path.exists()
    assert "# Synthetic Oracle Uplift Evaluation" in report_path.read_text(encoding="utf-8")


def test_missing_predicted_uplift_column_raises_clear_error(
    experiment_data: pd.DataFrame,
) -> None:
    with pytest.raises(
        ValueError,
        match="Missing evaluation columns: predicted_uplift",
    ):
        uplift_ranking_table(experiment_data)
