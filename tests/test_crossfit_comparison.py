from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.evaluation import (
    compare_uplift_models,
    crossfit_uplift_model,
    generate_comparison_report,
    oracle_score_baseline,
    random_score_baseline,
)
from causal_uplift_experimentation_ops.models import MODEL_REGISTRY

EXPECTED_MODELS = {
    "logistic_t_learner",
    "logistic_s_learner",
    "random_forest_t_learner",
    "random_baseline",
    "oracle_baseline",
}


@pytest.fixture(scope="module")
def experiment_data() -> pd.DataFrame:
    return generate_synthetic_experiment(n_users=600, seed=404)


@pytest.fixture(scope="module")
def logistic_crossfit(experiment_data: pd.DataFrame) -> pd.DataFrame:
    return crossfit_uplift_model(
        experiment_data,
        MODEL_REGISTRY["logistic_t_learner"],
        n_splits=3,
        seed=9,
    )


@pytest.fixture(scope="module")
def comparison_result(experiment_data: pd.DataFrame):
    return compare_uplift_models(
        experiment_data,
        n_splits=3,
        seed=9,
        n_bootstrap=5,
    )


def test_crossfit_returns_one_prediction_per_row(
    experiment_data: pd.DataFrame,
    logistic_crossfit: pd.DataFrame,
) -> None:
    assert len(logistic_crossfit) == len(experiment_data)
    assert logistic_crossfit["user_id"].tolist() == experiment_data["user_id"].tolist()
    assert logistic_crossfit["user_id"].is_unique


def test_crossfit_has_expected_folds(logistic_crossfit: pd.DataFrame) -> None:
    assert "fold" in logistic_crossfit.columns
    assert set(logistic_crossfit["fold"]) == {0, 1, 2}


def test_each_fold_has_both_treatment_groups(logistic_crossfit: pd.DataFrame) -> None:
    treatment_values = logistic_crossfit.groupby("fold")["treatment"].apply(set)

    assert treatment_values.apply(lambda values: values == {0, 1}).all()


def test_crossfit_excludes_leakage_features(logistic_crossfit: pd.DataFrame) -> None:
    features = logistic_crossfit.attrs["feature_columns"]

    assert {"user_id", "treatment", "conversion", "spend", "true_uplift"}.isdisjoint(
        features
    )


def test_logistic_s_learner_predictions_are_finite(comparison_result) -> None:
    predictions = comparison_result.scored_predictions["logistic_s_learner"]

    assert np.isfinite(predictions["predicted_uplift"]).all()


def test_random_forest_t_learner_predictions_are_finite(comparison_result) -> None:
    predictions = comparison_result.scored_predictions["random_forest_t_learner"]

    assert np.isfinite(predictions["predicted_uplift"]).all()


def test_comparison_contains_all_expected_models(comparison_result) -> None:
    assert set(comparison_result.comparison["model"]) == EXPECTED_MODELS


def test_random_baseline_is_deterministic(experiment_data: pd.DataFrame) -> None:
    first = random_score_baseline(experiment_data, n_splits=3, seed=18)
    second = random_score_baseline(experiment_data, n_splits=3, seed=18)

    pd.testing.assert_frame_equal(first, second)


def test_oracle_baseline_uses_true_uplift(experiment_data: pd.DataFrame) -> None:
    oracle = oracle_score_baseline(experiment_data, n_splits=3, seed=2)

    pd.testing.assert_series_equal(
        oracle["predicted_uplift"],
        experiment_data["true_uplift"],
        check_names=False,
    )


def test_comparison_metrics_are_finite(comparison_result) -> None:
    metric_columns = [
        "auuc",
        "qini_coefficient",
        "maximum_qini_gain",
        "top_10_percent_uplift",
        "top_20_percent_uplift",
        "top_30_percent_uplift",
    ]

    assert np.isfinite(comparison_result.comparison.loc[:, metric_columns]).all().all()


def test_uncertainty_has_qini_interval_columns(comparison_result) -> None:
    assert {"qini_lower", "qini_median", "qini_upper"}.issubset(
        comparison_result.uncertainty.columns
    )


def test_comparison_report_generation(
    experiment_data: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report_path = generate_comparison_report(
        experiment_data,
        tmp_path / "comparison.md",
        n_splits=3,
        n_bootstrap=3,
    )

    assert report_path.exists()
    assert "# Cross-Fitted Uplift Model Comparison" in report_path.read_text(encoding="utf-8")


def test_invalid_crossfit_fold_count_raises(experiment_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="n_splits must be at least 2"):
        crossfit_uplift_model(
            experiment_data,
            MODEL_REGISTRY["logistic_t_learner"],
            n_splits=1,
        )


def test_missing_crossfit_columns_raise_clear_error(experiment_data: pd.DataFrame) -> None:
    invalid = experiment_data.drop(columns="conversion")

    with pytest.raises(ValueError, match="Missing cross-fit columns: conversion"):
        crossfit_uplift_model(
            invalid,
            MODEL_REGISTRY["logistic_t_learner"],
            n_splits=3,
        )
