from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.evaluation import split_experiment_data
from causal_uplift_experimentation_ops.models import (
    LogisticTLearner,
    generate_t_learner_report,
)


@pytest.fixture(scope="module")
def experiment_split():
    data = generate_synthetic_experiment(n_users=1_000, seed=321)
    return split_experiment_data(data, test_size=0.3, seed=12)


@pytest.fixture(scope="module")
def fitted_model(experiment_split) -> LogisticTLearner:
    return LogisticTLearner(experiment_split.feature_columns, seed=12).fit(
        experiment_split.train
    )


def test_t_learner_fits_generated_data(fitted_model: LogisticTLearner) -> None:
    assert fitted_model.is_fitted


def test_prediction_contains_uplift(
    fitted_model: LogisticTLearner,
    experiment_split,
) -> None:
    predictions = fitted_model.predict(experiment_split.test)

    assert "predicted_uplift" in predictions.columns


def test_predicted_uplift_is_finite(
    fitted_model: LogisticTLearner,
    experiment_split,
) -> None:
    predictions = fitted_model.predict(experiment_split.test)

    assert np.isfinite(predictions["predicted_uplift"]).all()


def test_predicted_probabilities_are_valid(
    fitted_model: LogisticTLearner,
    experiment_split,
) -> None:
    predictions = fitted_model.predict(experiment_split.test)

    assert predictions["predicted_control_conversion"].between(0, 1).all()
    assert predictions["predicted_treatment_conversion"].between(0, 1).all()


def test_leakage_columns_are_excluded(experiment_split) -> None:
    forbidden = {"user_id", "treatment", "conversion", "spend", "true_uplift"}

    assert forbidden.isdisjoint(experiment_split.feature_columns)
    with pytest.raises(ValueError, match="Feature columns contain leakage: conversion"):
        LogisticTLearner([*experiment_split.feature_columns, "conversion"]).fit(
            experiment_split.train
        )


def test_model_scoring_is_deterministic(experiment_split) -> None:
    first_model = LogisticTLearner(experiment_split.feature_columns, seed=5).fit(
        experiment_split.train
    )
    second_model = LogisticTLearner(experiment_split.feature_columns, seed=5).fit(
        experiment_split.train
    )

    pd.testing.assert_frame_equal(
        first_model.predict(experiment_split.test),
        second_model.predict(experiment_split.test),
    )


def test_report_generation_creates_markdown(tmp_path: Path) -> None:
    data = generate_synthetic_experiment(n_users=1_000, seed=99)
    report_path = generate_t_learner_report(data, tmp_path / "t_learner.md")

    assert report_path.exists()
    assert "# Synthetic Logistic T-Learner Report" in report_path.read_text(encoding="utf-8")


def test_missing_feature_column_raises_clear_error(
    fitted_model: LogisticTLearner,
    experiment_split,
) -> None:
    data_without_age = experiment_split.test.drop(columns="age")

    with pytest.raises(ValueError, match="Missing feature columns: age"):
        fitted_model.predict(data_without_age)
