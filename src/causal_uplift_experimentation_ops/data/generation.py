"""Generate a deterministic synthetic randomized experiment."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data

DEFAULT_OUTPUT_PATH = Path("data/processed/synthetic_experiment.csv")


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def generate_synthetic_experiment(
    n_users: int = 10_000,
    seed: int = 42,
    treatment_probability: float = 0.5,
) -> pd.DataFrame:
    """Generate user-level data from a randomized experiment.

    Covariates affect baseline conversion and a heterogeneous treatment effect.
    ``true_uplift`` is the difference between each user's treated and untreated
    conversion probabilities, making it useful for validating future models.
    """
    if n_users < 2:
        raise ValueError("n_users must be at least 2")
    if not 0.0 < treatment_probability < 1.0:
        raise ValueError("treatment_probability must be between 0 and 1")

    rng = np.random.default_rng(seed)

    age = rng.integers(18, 81, size=n_users)
    prior_purchases = np.clip(rng.poisson(lam=3.0, size=n_users), 0, 20)
    avg_order_value = np.round(rng.lognormal(mean=np.log(75), sigma=0.4, size=n_users), 2)
    days_since_last_purchase = np.clip(
        rng.gamma(shape=2.0, scale=35.0, size=n_users).astype(int),
        0,
        365,
    )
    channel = rng.choice(
        ["email", "organic", "paid_search", "social"],
        size=n_users,
        p=[0.30, 0.25, 0.25, 0.20],
    )

    # Complete randomization keeps assignment independent of covariates while
    # ensuring that every generated experiment has treatment and control users.
    n_treated = min(max(round(n_users * treatment_probability), 1), n_users - 1)
    treatment = np.concatenate(
        [np.ones(n_treated, dtype=int), np.zeros(n_users - n_treated, dtype=int)]
    )
    rng.shuffle(treatment)

    channel_baseline_effect = pd.Series(channel).map(
        {"email": 0.20, "organic": 0.10, "paid_search": -0.05, "social": -0.15}
    ).to_numpy()
    baseline_log_odds = (
        -2.4
        + 0.16 * prior_purchases
        + 0.004 * (avg_order_value - 75)
        - 0.006 * days_since_last_purchase
        + 0.004 * (age - 40)
        + channel_baseline_effect
    )

    treatment_log_odds_effect = (
        0.35
        + 0.18 * (prior_purchases >= 4)
        - 0.25 * (days_since_last_purchase >= 100)
        + 0.15 * (channel == "email")
        - 0.10 * (channel == "paid_search")
    )
    control_probability = _sigmoid(baseline_log_odds)
    treated_probability = _sigmoid(baseline_log_odds + treatment_log_odds_effect)
    true_uplift = treated_probability - control_probability

    observed_probability = np.where(treatment == 1, treated_probability, control_probability)
    conversion = rng.binomial(1, observed_probability)
    order_amount = rng.lognormal(np.log(avg_order_value), sigma=0.25)
    spend = np.round(conversion * order_amount * (1 + 0.05 * treatment), 2)

    data = pd.DataFrame(
        {
            "user_id": np.arange(1, n_users + 1),
            "age": age,
            "prior_purchases": prior_purchases,
            "avg_order_value": avg_order_value,
            "days_since_last_purchase": days_since_last_purchase,
            "channel": channel,
            "treatment": treatment,
            "conversion": conversion,
            "spend": spend,
            "true_uplift": np.round(true_uplift, 6),
        }
    )
    validate_experiment_data(data)
    return data


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=10_000, help="Number of users to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Destination CSV path (default: {DEFAULT_OUTPUT_PATH})",
    )
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate a CSV dataset from command-line arguments."""
    options = _parse_args(args)
    data = generate_synthetic_experiment(n_users=options.rows, seed=options.seed)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(options.output, index=False)
    print(f"Wrote {len(data):,} rows to {options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
