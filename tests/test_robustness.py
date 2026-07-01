from pathlib import Path

import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.evaluation import (
    evaluate_t_learner_repeated_splits,
    generate_robustness_report,
    summarize_repeated_split_results,
)

REQUIRED_METRICS = {
    "seed",
    "train_rows",
    "test_rows",
    "auuc",
    "qini_coefficient",
    "maximum_qini_gain",
    "top_10_percent_uplift",
    "top_20_percent_uplift",
    "top_30_percent_uplift",
}


@pytest.fixture(scope="module")
def experiment_data() -> pd.DataFrame:
    return generate_synthetic_experiment(n_users=1_000, seed=222)


@pytest.fixture(scope="module")
def repeated_results(experiment_data: pd.DataFrame) -> pd.DataFrame:
    return evaluate_t_learner_repeated_splits(experiment_data, seeds=[0, 1, 2])


def test_repeated_evaluation_returns_one_row_per_seed(
    repeated_results: pd.DataFrame,
) -> None:
    assert repeated_results["seed"].tolist() == [0, 1, 2]
    assert len(repeated_results) == 3


def test_repeated_evaluation_is_deterministic(experiment_data: pd.DataFrame) -> None:
    first = evaluate_t_learner_repeated_splits(experiment_data, seeds=[5, 6])
    second = evaluate_t_learner_repeated_splits(experiment_data, seeds=[5, 6])

    pd.testing.assert_frame_equal(first, second)


def test_required_metric_columns_exist(repeated_results: pd.DataFrame) -> None:
    assert REQUIRED_METRICS.issubset(repeated_results.columns)


def test_summary_statistics_include_required_aggregates(
    repeated_results: pd.DataFrame,
) -> None:
    summary = summarize_repeated_split_results(repeated_results)

    assert {"metric", "mean", "std", "min", "max"}.issubset(
        summary.metric_statistics.columns
    )


def test_positive_qini_rate_is_valid(repeated_results: pd.DataFrame) -> None:
    summary = summarize_repeated_split_results(repeated_results)

    assert 0.0 <= summary.positive_qini_rate <= 1.0
    assert summary.positive_qini_runs <= summary.run_count


def test_report_generation_creates_markdown(
    experiment_data: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report_path = generate_robustness_report(
        experiment_data,
        tmp_path / "robustness.md",
        seeds=[0, 1],
    )

    assert report_path.exists()
    assert "# T-Learner Repeated-Split Robustness" in report_path.read_text(encoding="utf-8")


def test_empty_seed_list_raises_clear_error(experiment_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="seeds must contain at least one value"):
        evaluate_t_learner_repeated_splits(experiment_data, seeds=[])
