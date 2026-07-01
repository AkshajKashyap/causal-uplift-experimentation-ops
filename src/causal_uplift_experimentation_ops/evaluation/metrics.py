"""Simple uplift ranking, curve, and targeting metrics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


def _validate_evaluation_data(
    data: pd.DataFrame,
    treatment_column: str,
    outcome_column: str,
    score_column: str,
) -> None:
    required = {treatment_column, outcome_column, score_column}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing evaluation columns: {', '.join(missing)}")
    if data.loc[:, sorted(required)].isna().any().any():
        raise ValueError("Evaluation columns must not contain missing values")

    treatment_values = set(data[treatment_column].unique())
    if treatment_values != {0, 1}:
        raise ValueError(f"{treatment_column!r} must contain both binary values 0 and 1")

    outcome_values = set(data[outcome_column].unique())
    if not outcome_values.issubset({0, 1}):
        raise ValueError(f"{outcome_column!r} must contain only 0 and 1")

    if not is_numeric_dtype(data[score_column]) or not np.isfinite(data[score_column]).all():
        raise ValueError(f"{score_column!r} must contain only finite numeric values")


def _ranked_data(
    data: pd.DataFrame,
    treatment_column: str,
    outcome_column: str,
    score_column: str,
) -> pd.DataFrame:
    _validate_evaluation_data(data, treatment_column, outcome_column, score_column)
    return data.sort_values(score_column, ascending=False, kind="mergesort").reset_index(drop=True)


def _uplift_contributions(
    ranked: pd.DataFrame,
    treatment_column: str,
    outcome_column: str,
) -> np.ndarray:
    """Return inverse-propensity contributions whose mean estimates treatment effect."""
    propensity = float(ranked[treatment_column].mean())
    treatment = ranked[treatment_column].to_numpy()
    outcome = ranked[outcome_column].to_numpy()
    return np.where(
        treatment == 1,
        outcome / propensity,
        -outcome / (1 - propensity),
    )


def _trapezoidal_area(y_values: pd.Series, x_values: pd.Series) -> float:
    """Integrate a curve without relying on a version-specific NumPy alias."""
    y = y_values.to_numpy()
    x = x_values.to_numpy()
    return float(np.sum(np.diff(x) * (y[:-1] + y[1:]) / 2))


def uplift_ranking_table(
    data: pd.DataFrame,
    n_bins: int = 10,
    treatment_column: str = "treatment",
    outcome_column: str = "conversion",
    score_column: str = "predicted_uplift",
) -> pd.DataFrame:
    """Summarize observed treatment-control differences in equal-sized score bins.

    Bin 1 contains the highest predicted uplift. ``observed_uplift`` is the treated
    conversion rate minus the control conversion rate within each bin.
    """
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1")
    ranked = _ranked_data(data, treatment_column, outcome_column, score_column)
    if len(ranked) < n_bins:
        raise ValueError("n_bins cannot exceed the number of rows")

    ranked = ranked.copy()
    ranked["uplift_bin"] = np.floor(np.arange(len(ranked)) * n_bins / len(ranked)).astype(int) + 1

    records: list[dict[str, float | int]] = []
    for bin_number, group in ranked.groupby("uplift_bin", sort=True):
        treated = group[group[treatment_column] == 1]
        control = group[group[treatment_column] == 0]
        treated_rate = float(treated[outcome_column].mean())
        control_rate = float(control[outcome_column].mean())
        records.append(
            {
                "uplift_bin": int(bin_number),
                "row_count": len(group),
                "population_fraction": len(group) / len(ranked),
                "treated_count": len(treated),
                "control_count": len(control),
                "mean_predicted_uplift": float(group[score_column].mean()),
                "treated_outcome_rate": treated_rate,
                "control_outcome_rate": control_rate,
                "observed_uplift": treated_rate - control_rate,
            }
        )
    return pd.DataFrame.from_records(records)


def cumulative_uplift_curve(
    data: pd.DataFrame,
    treatment_column: str = "treatment",
    outcome_column: str = "conversion",
    score_column: str = "predicted_uplift",
) -> pd.DataFrame:
    """Return cumulative uplift gain as progressively more users are targeted.

    Rows are ordered by descending score. At each prefix, inverse-propensity
    contributions are summed and divided by the full evaluation population. The
    endpoint therefore equals the experiment-wide treatment-effect estimate.
    """
    ranked = _ranked_data(data, treatment_column, outcome_column, score_column)
    contributions = _uplift_contributions(ranked, treatment_column, outcome_column)
    targeted_count = np.arange(1, len(ranked) + 1)
    cumulative_sum = np.cumsum(contributions)

    return pd.DataFrame(
        {
            "targeted_count": np.concatenate(([0], targeted_count)),
            "population_fraction": np.concatenate(([0.0], targeted_count / len(ranked))),
            "cumulative_uplift_gain": np.concatenate(([0.0], cumulative_sum / len(ranked))),
            "cumulative_average_uplift": np.concatenate(
                ([0.0], cumulative_sum / targeted_count)
            ),
        }
    )


def auuc_score(
    data: pd.DataFrame,
    treatment_column: str = "treatment",
    outcome_column: str = "conversion",
    score_column: str = "predicted_uplift",
) -> float:
    """Return trapezoidal area under the cumulative uplift-gain curve."""
    curve = cumulative_uplift_curve(data, treatment_column, outcome_column, score_column)
    return _trapezoidal_area(
        curve["cumulative_uplift_gain"],
        curve["population_fraction"],
    )


def qini_curve(
    data: pd.DataFrame,
    treatment_column: str = "treatment",
    outcome_column: str = "conversion",
    score_column: str = "predicted_uplift",
) -> pd.DataFrame:
    """Return uplift gain above the straight-line random-targeting baseline."""
    curve = cumulative_uplift_curve(data, treatment_column, outcome_column, score_column)
    total_gain = float(curve["cumulative_uplift_gain"].iloc[-1])
    result = curve.loc[:, ["targeted_count", "population_fraction"]].copy()
    result["cumulative_uplift_gain"] = curve["cumulative_uplift_gain"]
    result["random_targeting_gain"] = result["population_fraction"] * total_gain
    result["qini_gain"] = result["cumulative_uplift_gain"] - result["random_targeting_gain"]
    return result


def qini_coefficient(
    data: pd.DataFrame,
    treatment_column: str = "treatment",
    outcome_column: str = "conversion",
    score_column: str = "predicted_uplift",
) -> float:
    """Return trapezoidal area between the uplift and random-targeting curves."""
    curve = qini_curve(data, treatment_column, outcome_column, score_column)
    return _trapezoidal_area(curve["qini_gain"], curve["population_fraction"])


def top_k_policy_summary(
    data: pd.DataFrame,
    fractions: Sequence[float] = (0.1, 0.2, 0.3),
    treatment_column: str = "treatment",
    outcome_column: str = "conversion",
    score_column: str = "predicted_uplift",
) -> pd.DataFrame:
    """Estimate uplift if the highest-scored fraction of users were targeted."""
    ranked = _ranked_data(data, treatment_column, outcome_column, score_column)
    contributions = _uplift_contributions(ranked, treatment_column, outcome_column)

    records: list[dict[str, float | int]] = []
    for fraction in fractions:
        if not 0.0 < fraction <= 1.0:
            raise ValueError("Targeting fractions must be between 0 and 1")
        targeted_count = max(1, int(np.ceil(len(ranked) * fraction)))
        targeted = ranked.iloc[:targeted_count]
        treated = targeted[targeted[treatment_column] == 1]
        control = targeted[targeted[treatment_column] == 0]
        estimated_uplift = float(contributions[:targeted_count].mean())
        records.append(
            {
                "target_fraction": float(fraction),
                "targeted_count": targeted_count,
                "treated_count": len(treated),
                "control_count": len(control),
                "treated_outcome_rate": float(treated[outcome_column].mean()),
                "control_outcome_rate": float(control[outcome_column].mean()),
                "estimated_uplift": estimated_uplift,
                "estimated_incremental_conversions": estimated_uplift * targeted_count,
            }
        )
    return pd.DataFrame.from_records(records)
