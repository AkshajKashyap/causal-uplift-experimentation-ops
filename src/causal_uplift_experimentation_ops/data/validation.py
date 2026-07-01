"""Validation helpers for randomized experiment datasets."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

REQUIRED_COLUMNS = (
    "user_id",
    "age",
    "prior_purchases",
    "avg_order_value",
    "days_since_last_purchase",
    "channel",
    "treatment",
    "conversion",
    "spend",
    "true_uplift",
)


def _validate_binary_column(data: pd.DataFrame, column: str) -> None:
    values = set(data[column].unique())
    if not values.issubset({0, 1}):
        raise ValueError(f"{column!r} must contain only 0 and 1")


def validate_experiment_data(data: pd.DataFrame) -> None:
    """Raise ``ValueError`` when an experiment dataset violates its contract."""
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    columns_with_nulls = data.loc[:, REQUIRED_COLUMNS].columns[
        data.loc[:, REQUIRED_COLUMNS].isna().any()
    ].tolist()
    if columns_with_nulls:
        raise ValueError(f"Required columns contain missing values: {', '.join(columns_with_nulls)}")

    _validate_binary_column(data, "treatment")
    _validate_binary_column(data, "conversion")

    for column in ("spend", "true_uplift"):
        if not is_numeric_dtype(data[column]):
            raise ValueError(f"{column!r} must be numeric")
        if not np.isfinite(data[column]).all():
            raise ValueError(f"{column!r} must contain only finite values")

    if (data["spend"] < 0).any():
        raise ValueError("'spend' must be non-negative")
