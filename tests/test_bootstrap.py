from pathlib import Path

import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.evaluation import (
    bootstrap_uplift_metrics,
    generate_bootstrap_report,
    split_experiment_data,
    summarize_bootstrap_results,
)
from causal_uplift_experimentation_ops.models import LogisticTLearner

REQUIRED_METRICS = {
    "bootstrap_id",
    "auuc",
    "qini_coefficient",
    "maximum_qini_gain",
    "top_10_percent_uplift",
    "top_20_percent_uplift",
    "top_30_percent_uplift",
}


@pytest.fixture(scope="module")
def experiment_data() -> pd.DataFrame:
    return generate_synthetic_experiment(n_users=1_000, seed=111)


@pytest.fixture(scope="module")
def scored_test_data(experiment_data: pd.DataFrame) -> pd.DataFrame:
    split = split_experiment_data(experiment_data, test_size=0.3, seed=8)
    model = LogisticTLearner(split.feature_columns, seed=8).fit(split.train)
    return model.predict(split.test)


@pytest.fixture(scope="module")
def bootstrap_results(scored_test_data: pd.DataFrame) -> pd.DataFrame:
    return bootstrap_uplift_metrics(scored_test_data, n_bootstrap=8, seed=3)


def test_bootstrap_returns_one_row_per_sample(bootstrap_results: pd.DataFrame) -> None:
    assert len(bootstrap_results) == 8
    assert bootstrap_results["bootstrap_id"].tolist() == list(range(8))


def test_bootstrap_is_deterministic(scored_test_data: pd.DataFrame) -> None:
    first = bootstrap_uplift_metrics(scored_test_data, n_bootstrap=5, seed=12)
    second = bootstrap_uplift_metrics(scored_test_data, n_bootstrap=5, seed=12)

    pd.testing.assert_frame_equal(first, second)


def test_required_metric_columns_exist(bootstrap_results: pd.DataFrame) -> None:
    assert REQUIRED_METRICS.issubset(bootstrap_results.columns)


def test_interval_summary_contains_required_statistics(
    bootstrap_results: pd.DataFrame,
) -> None:
    summary = summarize_bootstrap_results(bootstrap_results)

    assert {"metric", "mean", "std", "2.5%", "50%", "97.5%"}.issubset(
        summary.metric_statistics.columns
    )


def test_positive_qini_rate_is_valid(bootstrap_results: pd.DataFrame) -> None:
    summary = summarize_bootstrap_results(bootstrap_results)

    assert 0.0 <= summary.positive_qini_rate <= 1.0


def test_non_positive_bootstrap_count_raises_clear_error(
    scored_test_data: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="n_bootstrap must be greater than 0"):
        bootstrap_uplift_metrics(scored_test_data, n_bootstrap=0)


def test_missing_predicted_uplift_raises_clear_error(
    scored_test_data: pd.DataFrame,
) -> None:
    invalid = scored_test_data.drop(columns="predicted_uplift")

    with pytest.raises(ValueError, match="Missing evaluation columns: predicted_uplift"):
        bootstrap_uplift_metrics(invalid, n_bootstrap=2)


def test_report_generation_creates_markdown(
    experiment_data: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report_path = generate_bootstrap_report(
        experiment_data,
        tmp_path / "bootstrap.md",
        n_bootstrap=5,
    )

    assert report_path.exists()
    assert "# T-Learner Bootstrap Uncertainty" in report_path.read_text(encoding="utf-8")
