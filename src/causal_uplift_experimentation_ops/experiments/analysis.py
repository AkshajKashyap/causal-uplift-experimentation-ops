"""Descriptive and inferential statistics for a randomized binary A/B test."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from scipy.stats import norm

DEFAULT_NUMERIC_COVARIATES = (
    "age",
    "prior_purchases",
    "avg_order_value",
    "days_since_last_purchase",
)


@dataclass(frozen=True)
class ExperimentSummary:
    """Key estimates from a randomized binary-treatment experiment."""

    row_count: int
    control_count: int
    treatment_count: int
    control_conversion_rate: float
    treatment_conversion_rate: float
    control_average_spend: float
    treatment_average_spend: float
    conversion_treatment_effect: float
    conversion_relative_lift: float
    spend_treatment_effect: float
    conversion_ci_lower: float
    conversion_ci_upper: float
    conversion_p_value: float

    def to_frame(self) -> pd.DataFrame:
        """Return the summary as a two-column DataFrame."""
        values = asdict(self)
        return pd.DataFrame({"metric": list(values), "value": list(values.values())})


def _validate_analysis_data(data: pd.DataFrame) -> None:
    required = {"treatment", "conversion", "spend"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing analysis columns: {', '.join(missing)}")

    columns_with_nulls = data.loc[:, sorted(required)].columns[
        data.loc[:, sorted(required)].isna().any()
    ].tolist()
    if columns_with_nulls:
        raise ValueError(f"Analysis columns contain missing values: {', '.join(columns_with_nulls)}")

    treatment_values = set(data["treatment"].unique())
    if not treatment_values.issubset({0, 1}):
        raise ValueError("'treatment' must contain only 0 and 1")
    if treatment_values != {0, 1}:
        raise ValueError("'treatment' must contain both control (0) and treatment (1)")

    conversion_values = set(data["conversion"].unique())
    if not conversion_values.issubset({0, 1}):
        raise ValueError("'conversion' must contain only 0 and 1")

    if not is_numeric_dtype(data["spend"]) or not np.isfinite(data["spend"]).all():
        raise ValueError("'spend' must contain only finite numeric values")


def treatment_control_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return counts, conversion rates, and average spend for each group."""
    _validate_analysis_data(data)
    grouped = data.groupby("treatment", sort=True).agg(
        count=("treatment", "size"),
        conversion_rate=("conversion", "mean"),
        average_spend=("spend", "mean"),
    )
    grouped.index = pd.Index(["control", "treatment"], name="group")
    return grouped


def conversion_rate_by_group(data: pd.DataFrame) -> pd.Series:
    """Return conversion rates for control and treatment."""
    return treatment_control_summary(data)["conversion_rate"].copy()


def average_spend_by_group(data: pd.DataFrame) -> pd.Series:
    """Return average spend for control and treatment."""
    return treatment_control_summary(data)["average_spend"].copy()


def conversion_treatment_effect(data: pd.DataFrame) -> float:
    """Estimate the absolute conversion-rate difference: treatment minus control."""
    rates = conversion_rate_by_group(data)
    return float(rates["treatment"] - rates["control"])


def conversion_relative_lift(data: pd.DataFrame) -> float:
    """Estimate conversion lift relative to control; return NaN if control is zero."""
    rates = conversion_rate_by_group(data)
    control_rate = float(rates["control"])
    if control_rate == 0.0:
        return float("nan")
    return float((rates["treatment"] - control_rate) / control_rate)


def spend_treatment_effect(data: pd.DataFrame) -> float:
    """Estimate the average spend difference: treatment minus control."""
    spend = average_spend_by_group(data)
    return float(spend["treatment"] - spend["control"])


def conversion_rate_difference_confidence_interval(
    data: pd.DataFrame,
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """Return a Wald confidence interval for the conversion-rate difference."""
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0 and 1")

    summary = treatment_control_summary(data)
    control_rate = float(summary.loc["control", "conversion_rate"])
    treatment_rate = float(summary.loc["treatment", "conversion_rate"])
    control_count = int(summary.loc["control", "count"])
    treatment_count = int(summary.loc["treatment", "count"])

    difference = treatment_rate - control_rate
    standard_error = np.sqrt(
        treatment_rate * (1 - treatment_rate) / treatment_count
        + control_rate * (1 - control_rate) / control_count
    )
    critical_value = norm.ppf(1 - (1 - confidence_level) / 2)
    lower = max(-1.0, difference - critical_value * standard_error)
    upper = min(1.0, difference + critical_value * standard_error)
    return float(lower), float(upper)


def conversion_rate_difference_p_value(data: pd.DataFrame) -> float:
    """Return a two-sided pooled two-proportion z-test p-value."""
    summary = treatment_control_summary(data)
    control_rate = float(summary.loc["control", "conversion_rate"])
    treatment_rate = float(summary.loc["treatment", "conversion_rate"])
    control_count = int(summary.loc["control", "count"])
    treatment_count = int(summary.loc["treatment", "count"])

    pooled_rate = (
        control_rate * control_count + treatment_rate * treatment_count
    ) / (control_count + treatment_count)
    standard_error = np.sqrt(
        pooled_rate * (1 - pooled_rate) * (1 / control_count + 1 / treatment_count)
    )
    if standard_error == 0.0:
        return 1.0

    z_score = (treatment_rate - control_rate) / standard_error
    return float(2 * norm.sf(abs(z_score)))


def numeric_covariate_balance(
    data: pd.DataFrame,
    covariates: Sequence[str] = DEFAULT_NUMERIC_COVARIATES,
    threshold: float = 0.1,
) -> pd.DataFrame:
    """Compare numeric covariates using absolute standardized mean differences."""
    _validate_analysis_data(data)
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    missing = sorted(set(covariates) - set(data.columns))
    if missing:
        raise ValueError(f"Missing numeric covariates: {', '.join(missing)}")

    records: list[dict[str, object]] = []
    for covariate in covariates:
        if not is_numeric_dtype(data[covariate]):
            raise ValueError(f"{covariate!r} must be numeric")
        if data[covariate].isna().any() or not np.isfinite(data[covariate]).all():
            raise ValueError(f"{covariate!r} must contain only finite values")

        control = data.loc[data["treatment"] == 0, covariate]
        treatment = data.loc[data["treatment"] == 1, covariate]
        control_mean = float(control.mean())
        treatment_mean = float(treatment.mean())
        pooled_standard_deviation = np.sqrt((control.var() + treatment.var()) / 2)

        if pooled_standard_deviation == 0:
            standardized_difference = 0.0 if treatment_mean == control_mean else float("inf")
        else:
            standardized_difference = float(
                (treatment_mean - control_mean) / pooled_standard_deviation
            )
        absolute_difference = abs(standardized_difference)
        records.append(
            {
                "covariate": covariate,
                "control_mean": control_mean,
                "treatment_mean": treatment_mean,
                "standardized_mean_difference": standardized_difference,
                "absolute_standardized_mean_difference": absolute_difference,
                "balanced": absolute_difference <= threshold,
            }
        )

    return pd.DataFrame.from_records(records)


def summarize_experiment(
    data: pd.DataFrame,
    confidence_level: float = 0.95,
) -> ExperimentSummary:
    """Collect the baseline A/B estimates in one immutable summary object."""
    group_summary = treatment_control_summary(data)
    confidence_interval = conversion_rate_difference_confidence_interval(
        data,
        confidence_level=confidence_level,
    )
    return ExperimentSummary(
        row_count=len(data),
        control_count=int(group_summary.loc["control", "count"]),
        treatment_count=int(group_summary.loc["treatment", "count"]),
        control_conversion_rate=float(group_summary.loc["control", "conversion_rate"]),
        treatment_conversion_rate=float(group_summary.loc["treatment", "conversion_rate"]),
        control_average_spend=float(group_summary.loc["control", "average_spend"]),
        treatment_average_spend=float(group_summary.loc["treatment", "average_spend"]),
        conversion_treatment_effect=conversion_treatment_effect(data),
        conversion_relative_lift=conversion_relative_lift(data),
        spend_treatment_effect=spend_treatment_effect(data),
        conversion_ci_lower=confidence_interval[0],
        conversion_ci_upper=confidence_interval[1],
        conversion_p_value=conversion_rate_difference_p_value(data),
    )
