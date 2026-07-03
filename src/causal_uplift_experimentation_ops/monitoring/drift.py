"""Transparent input and prediction drift checks for offline staging batches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

SEVERITY_ORDER = {"pass": 0, "warn": 1, "fail": 2}


def worst_severity(values: pd.Series | list[str]) -> str:
    """Return the most severe status in a sequence."""
    statuses = list(values)
    return max(statuses, key=lambda value: SEVERITY_ORDER[value], default="pass")


def threshold_severity(
    value: float,
    warn_threshold: float,
    fail_threshold: float,
) -> str:
    if value >= fail_threshold:
        return "fail"
    if value >= warn_threshold:
        return "warn"
    return "pass"


def _record(
    *,
    feature: str,
    feature_type: str,
    metric_name: str,
    reference_value: float,
    current_value: float,
    severity: str,
    notes: str,
) -> dict[str, object]:
    return {
        "feature": feature,
        "feature_type": feature_type,
        "metric_name": metric_name,
        "reference_value": reference_value,
        "current_value": current_value,
        "absolute_difference": abs(current_value - reference_value),
        "severity": severity,
        "notes": notes,
    }


def _numeric_psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    reference_clean = reference.dropna().astype(float)
    current_clean = current.dropna().astype(float)
    if reference_clean.empty or current_clean.empty:
        return float("nan")
    edges = np.unique(
        np.quantile(reference_clean, np.linspace(0, 1, bins + 1))
    )
    if len(edges) < 2:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    reference_counts = np.histogram(reference_clean, bins=edges)[0]
    current_counts = np.histogram(current_clean, bins=edges)[0]
    reference_rate = np.clip(reference_counts / reference_counts.sum(), 1e-6, None)
    current_rate = np.clip(current_counts / current_counts.sum(), 1e-6, None)
    return float(
        np.sum((current_rate - reference_rate) * np.log(current_rate / reference_rate))
    )


def _categorical_psi(reference: pd.Series, current: pd.Series) -> float:
    reference_values = reference.fillna("<MISSING>").astype(str)
    current_values = current.fillna("<MISSING>").astype(str)
    categories = sorted(set(reference_values) | set(current_values))
    reference_rate = (
        reference_values.value_counts(normalize=True).reindex(categories, fill_value=0)
    )
    current_rate = (
        current_values.value_counts(normalize=True).reindex(categories, fill_value=0)
    )
    reference_rate = np.clip(reference_rate.to_numpy(), 1e-6, None)
    current_rate = np.clip(current_rate.to_numpy(), 1e-6, None)
    return float(
        np.sum((current_rate - reference_rate) * np.log(current_rate / reference_rate))
    )


def check_input_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    feature_columns: tuple[str, ...] | list[str] | None = None,
) -> pd.DataFrame:
    """Compare raw pre-score feature distributions with simple explainable metrics."""
    features = tuple(feature_columns or reference.columns)
    records: list[dict[str, object]] = []
    for feature in features:
        if feature not in reference:
            raise ValueError(f"Reference data is missing feature: {feature}")
        feature_type = "numeric" if is_numeric_dtype(reference[feature]) else "categorical"
        if feature not in current:
            records.append(
                _record(
                    feature=feature,
                    feature_type=feature_type,
                    metric_name="feature_present",
                    reference_value=1.0,
                    current_value=0.0,
                    severity="fail",
                    notes="Required feature is absent from current input.",
                )
            )
            continue

        reference_missing = float(reference[feature].isna().mean())
        current_missing = float(current[feature].isna().mean())
        missing_difference = abs(current_missing - reference_missing)
        records.append(
            _record(
                feature=feature,
                feature_type=feature_type,
                metric_name="missing_rate",
                reference_value=reference_missing,
                current_value=current_missing,
                severity=threshold_severity(missing_difference, 0.02, 0.10),
                notes="Absolute missing-rate change; warn >=2%, fail >=10%.",
            )
        )

        if feature_type == "numeric":
            reference_values = pd.to_numeric(reference[feature], errors="coerce")
            current_values = pd.to_numeric(current[feature], errors="coerce")
            reference_mean = float(reference_values.mean())
            current_mean = float(current_values.mean())
            reference_std = float(reference_values.std(ddof=0))
            current_std = float(current_values.std(ddof=0))
            standardized_shift = (
                abs(current_mean - reference_mean) / reference_std
                if reference_std > 0
                else float(current_mean != reference_mean)
            )
            records.append(
                _record(
                    feature=feature,
                    feature_type=feature_type,
                    metric_name="mean",
                    reference_value=reference_mean,
                    current_value=current_mean,
                    severity=threshold_severity(standardized_shift, 0.10, 0.25),
                    notes=(
                        f"Standardized mean shift={standardized_shift:.4f}; "
                        "warn >=0.10, fail >=0.25."
                    ),
                )
            )
            std_ratio = current_std / reference_std if reference_std > 0 else 1.0
            records.append(
                _record(
                    feature=feature,
                    feature_type=feature_type,
                    metric_name="standard_deviation_ratio",
                    reference_value=1.0,
                    current_value=std_ratio,
                    severity=threshold_severity(abs(std_ratio - 1), 0.20, 0.50),
                    notes="Ratio current/reference; warn shift >=0.20, fail >=0.50.",
                )
            )
            psi = _numeric_psi(reference_values, current_values)
        else:
            reference_values = reference[feature].fillna("<MISSING>").astype(str)
            current_values = current[feature].fillna("<MISSING>").astype(str)
            reference_categories = set(reference_values)
            unseen_rate = float((~current_values.isin(reference_categories)).mean())
            records.append(
                _record(
                    feature=feature,
                    feature_type=feature_type,
                    metric_name="unseen_category_rate",
                    reference_value=0.0,
                    current_value=unseen_rate,
                    severity=threshold_severity(unseen_rate, 0.01, 0.05),
                    notes="Current values absent from reference; warn >=1%, fail >=5%.",
                )
            )
            categories = sorted(reference_categories | set(current_values))
            reference_frequencies = reference_values.value_counts(normalize=True)
            current_frequencies = current_values.value_counts(normalize=True)
            for category in categories:
                reference_frequency = float(reference_frequencies.get(category, 0.0))
                current_frequency = float(current_frequencies.get(category, 0.0))
                difference = abs(current_frequency - reference_frequency)
                records.append(
                    _record(
                        feature=feature,
                        feature_type=feature_type,
                        metric_name=f"category_frequency:{category}",
                        reference_value=reference_frequency,
                        current_value=current_frequency,
                        severity=threshold_severity(difference, 0.05, 0.15),
                        notes="Absolute category-frequency change.",
                    )
                )
            psi = _categorical_psi(reference[feature], current[feature])

        records.append(
            _record(
                feature=feature,
                feature_type=feature_type,
                metric_name="population_stability_index",
                reference_value=0.0,
                current_value=psi,
                severity=(
                    "fail"
                    if not np.isfinite(psi)
                    else threshold_severity(psi, 0.10, 0.25)
                ),
                notes="PSI warn >=0.10, fail >=0.25.",
            )
        )
    return pd.DataFrame.from_records(records)


@dataclass(frozen=True)
class PredictionDriftResult:
    """Prediction distribution metrics plus aggregate status."""

    metrics: pd.DataFrame
    status: str


def summarize_prediction_drift(
    scored: pd.DataFrame,
    reference_scored: pd.DataFrame | None = None,
    treatment_cost_per_user: float = 1.0,
) -> PredictionDriftResult:
    """Summarize score/recommendation behavior and compare a reference distribution."""
    required = {"predicted_uplift", "recommended_treatment", "policy_eligible"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"Missing prediction drift columns: {', '.join(missing)}")
    if scored.empty:
        raise ValueError("Scored data must not be empty")
    if scored["predicted_uplift"].isna().any():
        raise ValueError("'predicted_uplift' must not contain missing values")
    if treatment_cost_per_user < 0:
        raise ValueError("treatment_cost_per_user must be non-negative")

    reference = reference_scored if reference_scored is not None else scored
    reference_missing = sorted(required - set(reference.columns))
    if reference_missing:
        raise ValueError(
            f"Missing reference prediction columns: {', '.join(reference_missing)}"
        )
    current_uplift = scored["predicted_uplift"].astype(float)
    reference_uplift = reference["predicted_uplift"].astype(float)
    records: list[dict[str, Any]] = []

    def add_metric(
        name: str,
        current_value: float,
        reference_value: float,
        severity: str = "pass",
        notes: str = "",
    ) -> None:
        records.append(
            {
                "metric_name": name,
                "reference_value": reference_value,
                "current_value": current_value,
                "absolute_difference": abs(current_value - reference_value),
                "severity": severity,
                "notes": notes,
            }
        )

    summary_functions = {
        "predicted_uplift_mean": lambda series: float(series.mean()),
        "predicted_uplift_std": lambda series: float(series.std(ddof=0)),
        "predicted_uplift_min": lambda series: float(series.min()),
        "predicted_uplift_max": lambda series: float(series.max()),
    }
    for name, function in summary_functions.items():
        current_value = function(current_uplift)
        reference_value = function(reference_uplift)
        difference = abs(current_value - reference_value)
        if name == "predicted_uplift_mean":
            severity = threshold_severity(difference, 0.01, 0.03)
        else:
            severity = "pass"
        add_metric(
            name,
            current_value,
            reference_value,
            severity,
            "Distribution summary; mean shift warn >=0.01, fail >=0.03.",
        )

    for quantile in (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99):
        add_metric(
            f"predicted_uplift_p{int(quantile * 100):02d}",
            float(current_uplift.quantile(quantile)),
            float(reference_uplift.quantile(quantile)),
        )

    current_recommendation_rate = float(scored["recommended_treatment"].mean())
    reference_recommendation_rate = float(reference["recommended_treatment"].mean())
    recommendation_shift = abs(
        current_recommendation_rate - reference_recommendation_rate
    )
    recommendation_severity = threshold_severity(
        recommendation_shift,
        0.05,
        0.15,
    )
    if recommendation_shift < 0.05 and (
        current_recommendation_rate > 0.99 or current_recommendation_rate < 0.01
    ):
        recommendation_severity = "warn"
    add_metric(
        "recommendation_rate",
        current_recommendation_rate,
        reference_recommendation_rate,
        recommendation_severity,
        "Shift warn >=5%, fail >=15%; extreme stable rates are still warned.",
    )
    add_metric(
        "policy_eligibility_rate",
        float(scored["policy_eligible"].mean()),
        float(reference["policy_eligible"].mean()),
    )
    for name, current_rate, reference_rate in (
        (
            "negative_score_rate",
            float((current_uplift < 0).mean()),
            float((reference_uplift < 0).mean()),
        ),
        (
            "positive_score_rate",
            float((current_uplift > 0).mean()),
            float((reference_uplift > 0).mean()),
        ),
    ):
        rate_shift = abs(current_rate - reference_rate)
        rate_severity = threshold_severity(rate_shift, 0.10, 0.25)
        if rate_shift < 0.10 and current_rate > 0.99:
            rate_severity = "warn"
        add_metric(
            name,
            current_rate,
            reference_rate,
            rate_severity,
            "Shift warn >=10%, fail >=25%; rates above 99% are warned.",
        )
    add_metric(
        "estimated_treatment_cost",
        float(scored["recommended_treatment"].sum() * treatment_cost_per_user),
        float(reference["recommended_treatment"].sum() * treatment_cost_per_user),
    )
    metrics = pd.DataFrame.from_records(records)
    return PredictionDriftResult(
        metrics=metrics,
        status=worst_severity(metrics["severity"]),
    )
