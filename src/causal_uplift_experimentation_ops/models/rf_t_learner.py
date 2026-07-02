"""Random-forest T-learner sharing the leakage-safe T-learner machinery."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sklearn.ensemble import RandomForestClassifier

from causal_uplift_experimentation_ops.models.t_learner import LogisticTLearner


class RandomForestTLearner(LogisticTLearner):
    """Fit separate random-forest outcome models for treatment and control."""

    def __init__(
        self,
        feature_columns: Sequence[str],
        treatment_column: str = "treatment",
        outcome_column: str = "conversion",
        seed: int = 42,
        n_estimators: int = 100,
    ) -> None:
        super().__init__(feature_columns, treatment_column, outcome_column, seed)
        self.n_estimators = n_estimators

    @property
    def _scale_numeric_features(self) -> bool:
        return False

    def _make_classifier(self) -> Any:
        return RandomForestClassifier(
            n_estimators=self.n_estimators,
            min_samples_leaf=10,
            random_state=self.seed,
            n_jobs=1,
        )
