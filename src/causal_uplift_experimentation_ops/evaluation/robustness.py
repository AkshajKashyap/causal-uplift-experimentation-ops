"""Repeated-split robustness evaluation for the logistic T-learner."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from causal_uplift_experimentation_ops.evaluation.metrics import (
    auuc_score,
    qini_coefficient,
    qini_curve,
    top_k_policy_summary,
)
from causal_uplift_experimentation_ops.evaluation.splitting import split_experiment_data
from causal_uplift_experimentation_ops.models.t_learner import LogisticTLearner

DEFAULT_ROBUSTNESS_SEEDS = (0, 1, 2, 3, 4)
ROBUSTNESS_METRIC_COLUMNS = (
    "auuc",
    "qini_coefficient",
    "maximum_qini_gain",
    "top_10_percent_uplift",
    "top_20_percent_uplift",
    "top_30_percent_uplift",
)
REQUIRED_RESULT_COLUMNS = ("seed", "train_rows", "test_rows", *ROBUSTNESS_METRIC_COLUMNS)


@dataclass(frozen=True)
class RobustnessSummary:
    """Aggregate performance and directional consistency across split seeds."""

    metric_statistics: pd.DataFrame
    run_count: int
    positive_qini_runs: int
    positive_qini_rate: float


def evaluate_t_learner_repeated_splits(
    data: pd.DataFrame,
    seeds: Sequence[int] = DEFAULT_ROBUSTNESS_SEEDS,
    test_size: float = 0.3,
) -> pd.DataFrame:
    """Fit and evaluate the existing T-learner once per deterministic split seed."""
    seed_values = tuple(seeds)
    if not seed_values:
        raise ValueError("seeds must contain at least one value")

    records: list[dict[str, float | int]] = []
    for seed in seed_values:
        split = split_experiment_data(data, test_size=test_size, seed=seed)
        model = LogisticTLearner(split.feature_columns, seed=seed).fit(split.train)
        predictions = model.predict(split.test)

        qini = qini_curve(predictions)
        policies = top_k_policy_summary(predictions).set_index("target_fraction")
        records.append(
            {
                "seed": int(seed),
                "train_rows": len(split.train),
                "test_rows": len(split.test),
                "auuc": auuc_score(predictions),
                "qini_coefficient": qini_coefficient(predictions),
                "maximum_qini_gain": float(qini["qini_gain"].max()),
                "top_10_percent_uplift": float(policies.loc[0.1, "estimated_uplift"]),
                "top_20_percent_uplift": float(policies.loc[0.2, "estimated_uplift"]),
                "top_30_percent_uplift": float(policies.loc[0.3, "estimated_uplift"]),
            }
        )
    return pd.DataFrame.from_records(records, columns=REQUIRED_RESULT_COLUMNS)


def summarize_repeated_split_results(results: pd.DataFrame) -> RobustnessSummary:
    """Summarize metric dispersion and the fraction of positive Qini runs."""
    if results.empty:
        raise ValueError("results must contain at least one run")

    missing = sorted(set(REQUIRED_RESULT_COLUMNS) - set(results.columns))
    if missing:
        raise ValueError(f"Missing robustness result columns: {', '.join(missing)}")

    statistics = pd.DataFrame(
        [
            {
                "metric": metric,
                "mean": float(results[metric].mean()),
                "std": float(results[metric].std(ddof=0)),
                "min": float(results[metric].min()),
                "max": float(results[metric].max()),
            }
            for metric in ROBUSTNESS_METRIC_COLUMNS
        ]
    )
    positive_qini_runs = int((results["qini_coefficient"] > 0).sum())
    run_count = len(results)
    return RobustnessSummary(
        metric_statistics=statistics,
        run_count=run_count,
        positive_qini_runs=positive_qini_runs,
        positive_qini_rate=positive_qini_runs / run_count,
    )
