"""Logistic-regression S-learner for binary conversion uplift."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from causal_uplift_experimentation_ops.models.t_learner import LEAKAGE_COLUMNS


class LogisticSLearner:
    """Fit one logistic outcome model with treatment as an explicit input."""

    def __init__(
        self,
        feature_columns: Sequence[str],
        treatment_column: str = "treatment",
        outcome_column: str = "conversion",
        seed: int = 42,
    ) -> None:
        self.feature_columns = tuple(feature_columns)
        self.treatment_column = treatment_column
        self.outcome_column = outcome_column
        self.seed = seed
        self.model: Pipeline | None = None

    @property
    def is_fitted(self) -> bool:
        return self.model is not None

    def _validate_features(self, data: pd.DataFrame) -> None:
        if not self.feature_columns:
            raise ValueError("At least one feature column is required")
        missing = sorted(set(self.feature_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Missing feature columns: {', '.join(missing)}")
        forbidden = LEAKAGE_COLUMNS | {self.treatment_column, self.outcome_column}
        leaked = sorted(set(self.feature_columns) & forbidden)
        if leaked:
            raise ValueError(f"Feature columns contain leakage: {', '.join(leaked)}")

    def fit(self, data: pd.DataFrame) -> LogisticSLearner:
        """Fit the shared conversion model on covariates plus treatment."""
        self._validate_features(data)
        required = {self.treatment_column, self.outcome_column}
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(f"Missing training columns: {', '.join(missing)}")
        if set(data[self.treatment_column].unique()) != {0, 1}:
            raise ValueError(f"{self.treatment_column!r} must contain both binary values 0 and 1")
        if not set(data[self.outcome_column].unique()).issubset({0, 1}):
            raise ValueError(f"{self.outcome_column!r} must contain only 0 and 1")
        if data[self.outcome_column].nunique() < 2:
            raise ValueError("Training rows must contain both conversion outcomes")

        numeric = [
            column for column in self.feature_columns if is_numeric_dtype(data[column])
        ]
        numeric.append(self.treatment_column)
        categorical = [
            column for column in self.feature_columns if column not in set(numeric)
        ]
        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    numeric,
                ),
                (
                    "categorical",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("encoder", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    categorical,
                ),
            ],
            remainder="drop",
        )
        self.model = Pipeline(
            [
                ("preprocessor", preprocessor),
                ("classifier", LogisticRegression(max_iter=1_000, random_state=self.seed)),
            ]
        )
        model_columns = [*self.feature_columns, self.treatment_column]
        self.model.fit(data.loc[:, model_columns], data[self.outcome_column])
        return self

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Score each row with treatment forced to zero and one."""
        if self.model is None:
            raise ValueError("S-learner must be fitted before prediction")
        self._validate_features(data)
        result_columns = ["user_id", self.treatment_column, self.outcome_column]
        missing = sorted(set(result_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Missing scoring columns: {', '.join(missing)}")

        control_features = data.loc[:, self.feature_columns].copy()
        treatment_features = control_features.copy()
        control_features[self.treatment_column] = 0
        treatment_features[self.treatment_column] = 1
        control_probability = self.model.predict_proba(control_features)[:, 1]
        treatment_probability = self.model.predict_proba(treatment_features)[:, 1]

        result = data.loc[:, result_columns].rename(
            columns={
                self.treatment_column: "treatment",
                self.outcome_column: "conversion",
            }
        )
        result["predicted_control_conversion"] = control_probability
        result["predicted_treatment_conversion"] = treatment_probability
        result["predicted_uplift"] = treatment_probability - control_probability
        if "true_uplift" in data.columns:
            result["true_uplift"] = data["true_uplift"].to_numpy()
        if not np.isfinite(result["predicted_uplift"]).all():
            raise ValueError("Model predictions must be finite")
        return result.reset_index(drop=True)
