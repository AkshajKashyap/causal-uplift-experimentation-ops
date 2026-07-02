"""Leakage-safe train/test splitting for randomized experiment data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split

DEFAULT_OUTCOME_COLUMNS = ("conversion", "spend")
DEFAULT_NON_FEATURE_COLUMNS = ("user_id", "treatment", "true_uplift")


@dataclass(frozen=True)
class ExperimentSplit:
    """Train/test rows plus the columns safe to use as model features."""

    train: pd.DataFrame
    test: pd.DataFrame
    feature_columns: tuple[str, ...]
    treatment_column: str
    outcome_columns: tuple[str, ...]


def resolve_feature_columns(
    data: pd.DataFrame,
    feature_columns: Sequence[str] | None = None,
    treatment_column: str = "treatment",
    outcome_columns: Sequence[str] = DEFAULT_OUTCOME_COLUMNS,
) -> tuple[str, ...]:
    """Resolve pre-treatment model features and reject known leakage columns."""
    outcomes = tuple(outcome_columns)
    excluded = set(DEFAULT_NON_FEATURE_COLUMNS) | set(outcomes) | {treatment_column}
    if feature_columns is None:
        features = tuple(column for column in data.columns if column not in excluded)
    else:
        features = tuple(feature_columns)
        missing_features = sorted(set(features) - set(data.columns))
        if missing_features:
            raise ValueError(f"Missing feature columns: {', '.join(missing_features)}")
        leaked = sorted(set(features) & excluded)
        if leaked:
            raise ValueError(f"Feature columns contain leakage: {', '.join(leaked)}")

    if not features:
        raise ValueError("At least one feature column is required")
    return features


def split_experiment_data(
    data: pd.DataFrame,
    test_size: float = 0.2,
    seed: int = 42,
    feature_columns: Sequence[str] | None = None,
    treatment_column: str = "treatment",
    outcome_columns: Sequence[str] = DEFAULT_OUTCOME_COLUMNS,
) -> ExperimentSplit:
    """Return a deterministic treatment-stratified split and safe feature metadata.

    Outcomes, treatment assignment, the user identifier, and synthetic ``true_uplift``
    are excluded from inferred features. Explicit feature lists are checked against the
    same leakage exclusions.
    """
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1")

    outcomes = tuple(outcome_columns)
    required = {treatment_column, *outcomes}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing split columns: {', '.join(missing)}")
    if data.loc[:, sorted(required)].isna().any().any():
        raise ValueError("Treatment and outcome columns must not contain missing values")

    treatment_values = set(data[treatment_column].unique())
    if not treatment_values.issubset({0, 1}):
        raise ValueError(f"{treatment_column!r} must contain only 0 and 1")
    if treatment_values != {0, 1}:
        raise ValueError(f"{treatment_column!r} must contain both treatment groups")
    if (data[treatment_column].value_counts() < 2).any():
        raise ValueError("Each treatment group needs at least two rows for splitting")

    features = resolve_feature_columns(
        data,
        feature_columns=feature_columns,
        treatment_column=treatment_column,
        outcome_columns=outcomes,
    )

    train, test = train_test_split(
        data,
        test_size=test_size,
        random_state=seed,
        shuffle=True,
        stratify=data[treatment_column],
    )
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)

    if set(train[treatment_column]) != {0, 1} or set(test[treatment_column]) != {0, 1}:
        raise ValueError("test_size must leave both treatment groups in train and test")

    return ExperimentSplit(
        train=train,
        test=test,
        feature_columns=features,
        treatment_column=treatment_column,
        outcome_columns=outcomes,
    )
