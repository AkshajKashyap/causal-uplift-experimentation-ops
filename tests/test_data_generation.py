import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import (
    REQUIRED_COLUMNS,
    generate_synthetic_experiment,
    validate_experiment_data,
)


def test_generation_is_deterministic() -> None:
    first = generate_synthetic_experiment(n_users=200, seed=123)
    second = generate_synthetic_experiment(n_users=200, seed=123)

    pd.testing.assert_frame_equal(first, second)


def test_generated_data_has_expected_schema() -> None:
    data = generate_synthetic_experiment(n_users=100, seed=7)

    assert tuple(data.columns) == REQUIRED_COLUMNS
    assert len(data) == 100
    assert data["user_id"].is_unique


def test_treatment_and_control_groups_are_present() -> None:
    data = generate_synthetic_experiment(n_users=500, seed=42)

    assert set(data["treatment"]) == {0, 1}


def test_validation_passes_for_generated_data() -> None:
    data = generate_synthetic_experiment(n_users=100, seed=99)

    assert validate_experiment_data(data) is None


def test_validation_fails_when_required_column_is_missing() -> None:
    data = generate_synthetic_experiment(n_users=100, seed=99).drop(columns="conversion")

    with pytest.raises(ValueError, match="Missing required columns: conversion"):
        validate_experiment_data(data)
