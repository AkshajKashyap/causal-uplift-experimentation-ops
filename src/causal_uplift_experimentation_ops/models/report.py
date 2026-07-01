"""Train and evaluate the logistic-regression T-learner on synthetic data."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.metrics import (
    auuc_score,
    qini_coefficient,
    qini_curve,
    top_k_policy_summary,
    uplift_ranking_table,
)
from causal_uplift_experimentation_ops.evaluation.oracle import add_oracle_uplift_score
from causal_uplift_experimentation_ops.evaluation.splitting import split_experiment_data
from causal_uplift_experimentation_ops.models.t_learner import LogisticTLearner

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/synthetic_t_learner_report.md")


def _split_counts(data: pd.DataFrame) -> tuple[int, int]:
    counts = data["treatment"].value_counts()
    return int(counts.loc[0]), int(counts.loc[1])


def _random_targeting_interpretation(qini_value: float) -> str:
    if qini_value > 0:
        return "The positive Qini-style coefficient indicates better ranking than random targeting."
    if qini_value < 0:
        return (
            "The negative Qini-style coefficient indicates that this fitted ranking did not beat "
            "random targeting on the held-out sample."
        )
    return "The zero Qini-style coefficient is equivalent to random targeting on this sample."


def render_t_learner_report(
    data: pd.DataFrame,
    test_size: float = 0.3,
    seed: int = 42,
    n_bins: int = 10,
) -> str:
    """Fit the baseline T-learner and render held-out evaluation as Markdown."""
    split = split_experiment_data(data, test_size=test_size, seed=seed)
    model = LogisticTLearner(split.feature_columns, seed=seed).fit(split.train)
    predictions = model.predict(split.test)

    ranking = uplift_ranking_table(predictions, n_bins=n_bins)
    policies = top_k_policy_summary(predictions)
    qini = qini_curve(predictions)
    auuc = auuc_score(predictions)
    qini_value = qini_coefficient(predictions)
    max_qini_row = qini.loc[qini["qini_gain"].idxmax()]

    oracle_predictions = add_oracle_uplift_score(split.test)
    oracle_auuc = auuc_score(oracle_predictions)
    oracle_qini = qini_coefficient(oracle_predictions)

    train_control, train_treatment = _split_counts(split.train)
    test_control, test_treatment = _split_counts(split.test)
    feature_text = ", ".join(f"`{column}`" for column in split.feature_columns)

    ranking_rows = "\n".join(
        "| {bin:.0f} | {count:.0f} | {score:+.4f} | {treated:.2%} | "
        "{control:.2%} | {uplift:+.2%} |".format(
            bin=row.uplift_bin,
            count=row.row_count,
            score=row.mean_predicted_uplift,
            treated=row.treated_outcome_rate,
            control=row.control_outcome_rate,
            uplift=row.observed_uplift,
        )
        for row in ranking.itertuples(index=False)
    )
    policy_rows = "\n".join(
        "| {fraction:.0%} | {count:.0f} | {treated:.0f} | {control:.0f} | "
        "{uplift:+.2%} | {incremental:+.2f} |".format(
            fraction=row.target_fraction,
            count=row.targeted_count,
            treated=row.treated_count,
            control=row.control_count,
            uplift=row.estimated_uplift,
            incremental=row.estimated_incremental_conversions,
        )
        for row in policies.itertuples(index=False)
    )

    return f"""# Synthetic Logistic T-Learner Report

## Scope

This baseline fits separate logistic conversion models to treated and control training rows.
Predicted uplift is the treated conversion probability minus the control conversion probability.
All metrics below use only the held-out test rows.

## Leakage-safe split

| Split | Rows | Control | Treatment |
| --- | ---: | ---: | ---: |
| Train | {len(split.train):,} | {train_control:,} | {train_treatment:,} |
| Test | {len(split.test):,} | {test_control:,} | {test_treatment:,} |

Feature columns: {feature_text}

Excluded from features: treatment, conversion, spend, user identifier, and synthetic true uplift.

## Test-set uplift ranking

Bin 1 contains the highest predicted uplift.

| Bin | Rows | Mean predicted uplift | Treated conversion | Control conversion | Observed uplift |
| ---: | ---: | ---: | ---: | ---: | ---: |
{ranking_rows}

## Curve metrics

| Metric | T-learner | Synthetic oracle |
| --- | ---: | ---: |
| AUUC-style area | {auuc:.6f} | {oracle_auuc:.6f} |
| Qini-style coefficient | {qini_value:.6f} | {oracle_qini:.6f} |

- Maximum T-learner Qini gain: {max_qini_row["qini_gain"]:.6f} at {max_qini_row["population_fraction"]:.1%} targeted
- Random-targeting assessment: {_random_targeting_interpretation(qini_value)}

## Top-k targeting

| Targeted | Users | Treated | Control | Estimated uplift | Incremental conversions |
| ---: | ---: | ---: | ---: | ---: | ---: |
{policy_rows}

## Interpretation

This is a first linear-logit ranking baseline built from two logistic outcome models.
{_random_targeting_interpretation(qini_value)}

The oracle comparison is available only because this is synthetic data. Finite-sample metrics use
noisy observed binary outcomes, so the oracle ordering is not guaranteed to maximize every
realized test-set curve. The T-learner does not quantify uncertainty, tune hyperparameters, or
capture arbitrary nonlinear treatment-effect patterns, so results should be treated as a
benchmark rather than a production targeting policy.
"""


def generate_t_learner_report(
    data: pd.DataFrame,
    output_path: Path | str,
    test_size: float = 0.3,
    seed: int = 42,
    n_bins: int = 10,
) -> Path:
    """Write a held-out logistic T-learner evaluation report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = render_t_learner_report(
        data,
        test_size=test_size,
        seed=seed,
        n_bins=n_bins,
    )
    destination.write_text(report, encoding="utf-8")
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bins", type=int, default=10)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read synthetic data and write a held-out T-learner report."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    report_path = generate_t_learner_report(
        data,
        options.output,
        test_size=options.test_size,
        seed=options.seed,
        n_bins=options.bins,
    )
    print(f"Wrote T-learner report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
