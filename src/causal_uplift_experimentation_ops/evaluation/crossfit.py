"""Leakage-safe cross-fitted scoring for custom uplift models."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from causal_uplift_experimentation_ops.evaluation.oracle import add_oracle_uplift_score
from causal_uplift_experimentation_ops.evaluation.splitting import resolve_feature_columns
from causal_uplift_experimentation_ops.models.registry import ModelFactory


def stratified_fold_assignments(
    data: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
    treatment_column: str = "treatment",
) -> np.ndarray:
    """Return deterministic fold numbers stratified by treatment assignment."""
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if treatment_column not in data.columns:
        raise ValueError(f"Missing cross-fit columns: {treatment_column}")

    treatment_values = set(data[treatment_column].dropna().unique())
    if treatment_values != {0, 1}:
        raise ValueError(f"{treatment_column!r} must contain both binary values 0 and 1")
    if (data[treatment_column].value_counts() < n_splits).any():
        raise ValueError("Each treatment group must have at least n_splits rows")

    folds = np.empty(len(data), dtype=int)
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fold, (_, validation_positions) in enumerate(
        splitter.split(np.zeros(len(data)), data[treatment_column])
    ):
        folds[validation_positions] = fold
    return folds


def crossfit_uplift_model(
    data: pd.DataFrame,
    model_factory: ModelFactory,
    n_splits: int = 5,
    seed: int = 42,
    feature_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return one out-of-fold uplift prediction for every input row."""
    required = {"user_id", "treatment", "conversion"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing cross-fit columns: {', '.join(missing)}")
    if data.loc[:, sorted(required)].isna().any().any():
        raise ValueError("Cross-fit columns must not contain missing values")
    if not set(data["conversion"].unique()).issubset({0, 1}):
        raise ValueError("'conversion' must contain only 0 and 1")

    features = resolve_feature_columns(data, feature_columns=feature_columns)
    folds = stratified_fold_assignments(data, n_splits=n_splits, seed=seed)
    scored_folds: list[pd.DataFrame] = []

    for fold in range(n_splits):
        validation_positions = np.flatnonzero(folds == fold)
        training_positions = np.flatnonzero(folds != fold)
        training_data = data.iloc[training_positions]
        validation_data = data.iloc[validation_positions]
        if set(validation_data["treatment"]) != {0, 1}:
            raise ValueError(f"Fold {fold} must contain both treatment groups")

        model = model_factory(features, seed + fold)
        model.fit(training_data)
        predictions = model.predict(validation_data)
        predictions["fold"] = fold
        predictions["_row_position"] = validation_positions
        scored_folds.append(predictions)

    scored = (
        pd.concat(scored_folds, ignore_index=True)
        .sort_values("_row_position")
        .drop(columns="_row_position")
        .reset_index(drop=True)
    )
    if len(scored) != len(data) or scored["user_id"].tolist() != data["user_id"].tolist():
        raise RuntimeError("Cross-fitting did not produce exactly one prediction per input row")
    scored.attrs["feature_columns"] = features
    return scored


def random_score_baseline(
    data: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """Return deterministic random uplift scores with fold metadata."""
    required = {"user_id", "treatment", "conversion"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing baseline columns: {', '.join(missing)}")
    result = data.loc[:, ["user_id", "treatment", "conversion"]].copy()
    result["predicted_uplift"] = np.random.default_rng(seed).random(len(data))
    if "true_uplift" in data.columns:
        result["true_uplift"] = data["true_uplift"].to_numpy()
    result["fold"] = stratified_fold_assignments(data, n_splits=n_splits, seed=seed)
    return result


def oracle_score_baseline(
    data: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """Return synthetic true uplift as a benchmark score with fold metadata."""
    scored = add_oracle_uplift_score(data)
    result_columns = ["user_id", "treatment", "conversion", "predicted_uplift", "true_uplift"]
    result = scored.loc[:, result_columns].copy()
    result["fold"] = stratified_fold_assignments(data, n_splits=n_splits, seed=seed)
    return result
