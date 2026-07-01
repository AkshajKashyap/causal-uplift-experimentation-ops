"""Bootstrap uncertainty for uplift metrics on a fixed scored test set."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.evaluation.metrics import (
    auuc_score,
    qini_coefficient,
    qini_curve,
    top_k_policy_summary,
)

BOOTSTRAP_METRIC_COLUMNS = (
    "auuc",
    "qini_coefficient",
    "maximum_qini_gain",
    "top_10_percent_uplift",
    "top_20_percent_uplift",
    "top_30_percent_uplift",
)
REQUIRED_BOOTSTRAP_COLUMNS = ("bootstrap_id", *BOOTSTRAP_METRIC_COLUMNS)


@dataclass(frozen=True)
class BootstrapSummary:
    """Percentile uncertainty and directional consistency across bootstrap samples."""

    metric_statistics: pd.DataFrame
    sample_count: int
    positive_qini_samples: int
    positive_qini_rate: float


def bootstrap_uplift_metrics(
    scored_data: pd.DataFrame,
    n_bootstrap: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """Resample scored test rows within treatment arms and recompute uplift metrics.

    Stratifying the row bootstrap by observed treatment preserves both randomized
    arms and their original sample sizes in every replicate.
    """
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be greater than 0")

    # Validate the required treatment, outcome, and score contract before sampling.
    qini_curve(scored_data)

    control_positions = np.flatnonzero(scored_data["treatment"].to_numpy() == 0)
    treatment_positions = np.flatnonzero(scored_data["treatment"].to_numpy() == 1)
    rng = np.random.default_rng(seed)

    records: list[dict[str, float | int]] = []
    for bootstrap_id in range(n_bootstrap):
        sampled_positions = np.concatenate(
            (
                rng.choice(control_positions, size=len(control_positions), replace=True),
                rng.choice(treatment_positions, size=len(treatment_positions), replace=True),
            )
        )
        sampled_positions = rng.permutation(sampled_positions)
        sample = scored_data.iloc[sampled_positions].reset_index(drop=True)

        qini = qini_curve(sample)
        policies = top_k_policy_summary(sample).set_index("target_fraction")
        records.append(
            {
                "bootstrap_id": bootstrap_id,
                "auuc": auuc_score(sample),
                "qini_coefficient": qini_coefficient(sample),
                "maximum_qini_gain": float(qini["qini_gain"].max()),
                "top_10_percent_uplift": float(policies.loc[0.1, "estimated_uplift"]),
                "top_20_percent_uplift": float(policies.loc[0.2, "estimated_uplift"]),
                "top_30_percent_uplift": float(policies.loc[0.3, "estimated_uplift"]),
            }
        )
    return pd.DataFrame.from_records(records, columns=REQUIRED_BOOTSTRAP_COLUMNS)


def summarize_bootstrap_results(results: pd.DataFrame) -> BootstrapSummary:
    """Return percentile summaries and the fraction of positive Qini replicates."""
    if results.empty:
        raise ValueError("results must contain at least one bootstrap sample")

    missing = sorted(set(REQUIRED_BOOTSTRAP_COLUMNS) - set(results.columns))
    if missing:
        raise ValueError(f"Missing bootstrap result columns: {', '.join(missing)}")

    statistics = pd.DataFrame(
        [
            {
                "metric": metric,
                "mean": float(results[metric].mean()),
                "std": float(results[metric].std(ddof=0)),
                "2.5%": float(results[metric].quantile(0.025)),
                "50%": float(results[metric].quantile(0.5)),
                "97.5%": float(results[metric].quantile(0.975)),
            }
            for metric in BOOTSTRAP_METRIC_COLUMNS
        ]
    )
    positive_qini_samples = int((results["qini_coefficient"] > 0).sum())
    sample_count = len(results)
    return BootstrapSummary(
        metric_statistics=statistics,
        sample_count=sample_count,
        positive_qini_samples=positive_qini_samples,
        positive_qini_rate=positive_qini_samples / sample_count,
    )
