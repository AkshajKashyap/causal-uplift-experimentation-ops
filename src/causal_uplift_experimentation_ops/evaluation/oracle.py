"""Oracle scoring helpers used only to validate synthetic evaluation data."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


def add_oracle_uplift_score(
    data: pd.DataFrame,
    true_uplift_column: str = "true_uplift",
    score_column: str = "predicted_uplift",
) -> pd.DataFrame:
    """Copy synthetic true uplift into a score column for protocol validation.

    This helper is not a fitted model and must not be used for real-world scoring.
    """
    if true_uplift_column not in data.columns:
        raise ValueError(f"Missing oracle uplift column: {true_uplift_column}")
    if not is_numeric_dtype(data[true_uplift_column]):
        raise ValueError(f"{true_uplift_column!r} must be numeric")
    if data[true_uplift_column].isna().any() or not np.isfinite(data[true_uplift_column]).all():
        raise ValueError(f"{true_uplift_column!r} must contain only finite values")

    scored = data.copy()
    scored[score_column] = scored[true_uplift_column].astype(float)
    return scored
