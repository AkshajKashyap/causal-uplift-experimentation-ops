"""Shared interface for custom uplift models."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class UpliftModel(Protocol):
    """Minimal contract required by cross-fitted uplift evaluation."""

    feature_columns: tuple[str, ...]

    def fit(self, data: pd.DataFrame) -> UpliftModel:
        """Fit on randomized experiment rows."""
        ...

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return potential-outcome probabilities and predicted uplift."""
        ...
