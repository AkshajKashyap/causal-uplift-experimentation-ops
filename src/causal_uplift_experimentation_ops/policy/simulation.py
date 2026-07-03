"""Targeting-policy selection and within-model policy comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from causal_uplift_experimentation_ops.policy.value import (
    PolicyOutcome,
    PolicyValueConfig,
    estimate_policy_value,
)

DEFAULT_POLICY_NAMES = (
    "top_10_percent",
    "top_20_percent",
    "top_30_percent",
    "positive_uplift",
    "random_matched_20_percent",
    "oracle_matched_20_percent",
)
LEARNED_POLICY_NAMES = (
    "top_10_percent",
    "top_20_percent",
    "top_30_percent",
    "positive_uplift",
)


def _validate_scored_data(scored: pd.DataFrame) -> None:
    required = {"user_id", "treatment", "conversion", "predicted_uplift"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"Missing policy columns: {', '.join(missing)}")
    if not is_numeric_dtype(scored["predicted_uplift"]):
        raise ValueError("'predicted_uplift' must be numeric")
    if scored["predicted_uplift"].isna().any() or not np.isfinite(
        scored["predicted_uplift"]
    ).all():
        raise ValueError("'predicted_uplift' must contain only finite values")


def _eligible_rows(
    scored: pd.DataFrame,
    config: PolicyValueConfig,
    ranking_column: str = "predicted_uplift",
) -> pd.DataFrame:
    eligible = scored
    if config.min_predicted_uplift is not None:
        eligible = eligible[eligible[ranking_column] >= config.min_predicted_uplift]
    return eligible


def _limit_selection(
    selected: pd.DataFrame,
    population_size: int,
    config: PolicyValueConfig,
) -> pd.DataFrame:
    limit = config.maximum_users(population_size)
    return selected.iloc[:limit].copy().reset_index(drop=True)


def target_top_fraction(
    scored: pd.DataFrame,
    fraction: float,
    config: PolicyValueConfig | None = None,
) -> pd.DataFrame:
    """Select the highest predicted-uplift fraction, subject to constraints."""
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be between 0 and 1")
    _validate_scored_data(scored)
    assumptions = config or PolicyValueConfig()
    eligible = _eligible_rows(scored, assumptions)
    requested = int(np.ceil(len(scored) * fraction))
    ranked = eligible.sort_values("predicted_uplift", ascending=False, kind="mergesort")
    return _limit_selection(ranked.iloc[:requested], len(scored), assumptions)


def target_top_k(
    scored: pd.DataFrame,
    k: int,
    config: PolicyValueConfig | None = None,
) -> pd.DataFrame:
    """Select the highest predicted-uplift K users, subject to constraints."""
    if k < 0:
        raise ValueError("k must be non-negative")
    _validate_scored_data(scored)
    assumptions = config or PolicyValueConfig()
    eligible = _eligible_rows(scored, assumptions)
    ranked = eligible.sort_values("predicted_uplift", ascending=False, kind="mergesort")
    return _limit_selection(ranked.iloc[:k], len(scored), assumptions)


def target_positive_uplift(
    scored: pd.DataFrame,
    config: PolicyValueConfig | None = None,
) -> pd.DataFrame:
    """Select users whose predicted uplift is strictly positive."""
    _validate_scored_data(scored)
    assumptions = config or PolicyValueConfig()
    eligible = _eligible_rows(scored, assumptions)
    positive = eligible[eligible["predicted_uplift"] > 0].sort_values(
        "predicted_uplift",
        ascending=False,
        kind="mergesort",
    )
    return _limit_selection(positive, len(scored), assumptions)


def random_policy(
    scored: pd.DataFrame,
    selected_users: int,
    seed: int = 42,
    config: PolicyValueConfig | None = None,
) -> pd.DataFrame:
    """Select a deterministic random set of eligible users."""
    if selected_users < 0:
        raise ValueError("selected_users must be non-negative")
    _validate_scored_data(scored)
    assumptions = config or PolicyValueConfig()
    eligible = _eligible_rows(scored, assumptions)
    count = min(selected_users, len(eligible), assumptions.maximum_users(len(scored)))
    if count == 0:
        return eligible.iloc[:0].copy().reset_index(drop=True)
    positions = np.random.default_rng(seed).choice(len(eligible), size=count, replace=False)
    return eligible.iloc[positions].copy().reset_index(drop=True)


def oracle_policy(
    scored: pd.DataFrame,
    selected_users: int,
    config: PolicyValueConfig | None = None,
) -> pd.DataFrame:
    """Select top synthetic true-uplift users; unavailable for real data."""
    _validate_scored_data(scored)
    if "true_uplift" not in scored.columns:
        raise ValueError("Oracle policy requires 'true_uplift'")
    if selected_users < 0:
        raise ValueError("selected_users must be non-negative")
    assumptions = config or PolicyValueConfig()
    eligible = _eligible_rows(scored, assumptions, ranking_column="true_uplift")
    ranked = eligible.sort_values("true_uplift", ascending=False, kind="mergesort")
    return _limit_selection(ranked.iloc[:selected_users], len(scored), assumptions)


def compare_policies(
    scored: pd.DataFrame,
    config: PolicyValueConfig | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Evaluate standard depth, positive, random, and synthetic oracle policies."""
    _validate_scored_data(scored)
    assumptions = config or PolicyValueConfig()
    population_size = len(scored)
    selections: list[tuple[str, pd.DataFrame, str]] = []
    for fraction, name in (
        (0.1, "top_10_percent"),
        (0.2, "top_20_percent"),
        (0.3, "top_30_percent"),
    ):
        selections.append(
            (
                name,
                target_top_fraction(scored, fraction, assumptions),
                f"Top {fraction:.0%} by predicted uplift",
            )
        )

    top_twenty_count = len(selections[1][1])
    selections.extend(
        [
            (
                "positive_uplift",
                target_positive_uplift(scored, assumptions),
                "Predicted uplift greater than zero",
            ),
            (
                "random_matched_20_percent",
                random_policy(scored, top_twenty_count, seed=seed, config=assumptions),
                "Deterministic random policy matched to top-20% count",
            ),
        ]
    )
    if "true_uplift" in scored.columns:
        selections.append(
            (
                "oracle_matched_20_percent",
                oracle_policy(scored, top_twenty_count, assumptions),
                "Synthetic-only true-uplift policy matched to top-20% count",
            )
        )

    outcomes: list[PolicyOutcome] = [
        estimate_policy_value(
            selected,
            population_size=population_size,
            config=assumptions,
            policy_name=name,
            notes=notes,
        )
        for name, selected, notes in selections
    ]
    return pd.DataFrame.from_records([outcome.to_dict() for outcome in outcomes])
