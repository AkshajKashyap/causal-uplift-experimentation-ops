"""A leakage-safe logistic-regression T-learner for binary conversion."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

LEAKAGE_COLUMNS = {
    "user_id",
    "treatment",
    "conversion",
    "spend",
    "true_uplift",
    "predicted_control_conversion",
    "predicted_treatment_conversion",
    "predicted_uplift",
}


class LogisticTLearner:
    """Fit separate logistic outcome models for treatment and control."""

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
        self.numeric_feature_columns: tuple[str, ...] = ()
        self.categorical_feature_columns: tuple[str, ...] = ()
        self.control_model: Pipeline | None = None
        self.treatment_model: Pipeline | None = None

    @property
    def _scale_numeric_features(self) -> bool:
        return True

    def _make_classifier(self) -> Any:
        return LogisticRegression(max_iter=1_000, random_state=self.seed)

    @property
    def is_fitted(self) -> bool:
        """Return whether both arm-specific models have been fitted."""
        return self.control_model is not None and self.treatment_model is not None

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

    def _build_pipeline(self) -> Pipeline:
        transformers: list[tuple[str, Pipeline, list[str]]] = []
        if self.numeric_feature_columns:
            numeric_steps: list[tuple[str, Any]] = [
                ("imputer", SimpleImputer(strategy="median"))
            ]
            if self._scale_numeric_features:
                numeric_steps.append(("scaler", StandardScaler()))
            numeric_pipeline = Pipeline(
                steps=numeric_steps
            )
            transformers.append(
                ("numeric", numeric_pipeline, list(self.numeric_feature_columns))
            )
        if self.categorical_feature_columns:
            categorical_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore")),
                ]
            )
            transformers.append(
                ("categorical", categorical_pipeline, list(self.categorical_feature_columns))
            )

        preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
        return Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", self._make_classifier()),
            ]
        )

    def fit(self, data: pd.DataFrame) -> LogisticTLearner:
        """Fit one conversion model in each randomized treatment arm."""
        self._validate_features(data)
        required = {self.treatment_column, self.outcome_column}
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(f"Missing training columns: {', '.join(missing)}")
        if data.loc[:, sorted(required)].isna().any().any():
            raise ValueError("Treatment and outcome columns must not contain missing values")

        treatment_values = set(data[self.treatment_column].unique())
        if treatment_values != {0, 1}:
            raise ValueError(f"{self.treatment_column!r} must contain both binary values 0 and 1")
        outcome_values = set(data[self.outcome_column].unique())
        if not outcome_values.issubset({0, 1}):
            raise ValueError(f"{self.outcome_column!r} must contain only 0 and 1")

        self.numeric_feature_columns = tuple(
            column for column in self.feature_columns if is_numeric_dtype(data[column])
        )
        self.categorical_feature_columns = tuple(
            column for column in self.feature_columns if column not in self.numeric_feature_columns
        )

        control_rows = data[data[self.treatment_column] == 0]
        treatment_rows = data[data[self.treatment_column] == 1]
        for arm_name, arm_data in (("control", control_rows), ("treatment", treatment_rows)):
            if arm_data[self.outcome_column].nunique() < 2:
                raise ValueError(f"{arm_name} rows must contain both conversion outcomes")

        self.control_model = self._build_pipeline()
        self.treatment_model = self._build_pipeline()
        self.control_model.fit(
            control_rows.loc[:, self.feature_columns],
            control_rows[self.outcome_column],
        )
        self.treatment_model.fit(
            treatment_rows.loc[:, self.feature_columns],
            treatment_rows[self.outcome_column],
        )
        return self

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return both potential conversion predictions and their difference."""
        if not self.is_fitted:
            raise ValueError("T-learner must be fitted before prediction")
        self._validate_features(data)

        result_columns = ["user_id", self.treatment_column, self.outcome_column]
        missing = sorted(set(result_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Missing scoring columns: {', '.join(missing)}")

        features = data.loc[:, self.feature_columns]
        if self.control_model is None or self.treatment_model is None:
            raise RuntimeError("Fitted model state is inconsistent")
        control_probability = self.control_model.predict_proba(features)[:, 1]
        treatment_probability = self.treatment_model.predict_proba(features)[:, 1]

        result = data.loc[:, result_columns].copy()
        result = result.rename(
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

        prediction_columns = (
            "predicted_control_conversion",
            "predicted_treatment_conversion",
            "predicted_uplift",
        )
        if not np.isfinite(result.loc[:, prediction_columns]).all().all():
            raise ValueError("Model predictions must be finite")
        return result.reset_index(drop=True)
