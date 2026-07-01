"""Generate an oracle-based uplift evaluation report for synthetic data."""

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

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/synthetic_uplift_evaluation.md")


def _split_counts(data: pd.DataFrame) -> tuple[int, int]:
    counts = data["treatment"].value_counts()
    return int(counts.loc[0]), int(counts.loc[1])


def render_uplift_evaluation_report(
    data: pd.DataFrame,
    test_size: float = 0.3,
    seed: int = 42,
    n_bins: int = 10,
) -> str:
    """Split synthetic data and render oracle uplift evaluation as Markdown."""
    split = split_experiment_data(data, test_size=test_size, seed=seed)
    scored_test = add_oracle_uplift_score(split.test)
    ranking = uplift_ranking_table(scored_test, n_bins=n_bins)
    policies = top_k_policy_summary(scored_test)
    qini = qini_curve(scored_test)
    auuc = auuc_score(scored_test)
    qini_value = qini_coefficient(scored_test)

    train_control, train_treatment = _split_counts(split.train)
    test_control, test_treatment = _split_counts(split.test)
    max_qini_row = qini.loc[qini["qini_gain"].idxmax()]

    ranking_rows = "\n".join(
        "| {bin:.0f} | {count:.0f} | {score:.4f} | {treated:.2%} | "
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
    features = ", ".join(f"`{column}`" for column in split.feature_columns)

    return f"""# Synthetic Oracle Uplift Evaluation

## Scope

This is an evaluation-protocol check using the synthetic dataset's known `true_uplift` as an
oracle score. It is not a trained model and its metrics must not be interpreted as real model
performance.

## Leakage-safe split

| Split | Rows | Control | Treatment |
| --- | ---: | ---: | ---: |
| Train | {len(split.train):,} | {train_control:,} | {train_treatment:,} |
| Test | {len(split.test):,} | {test_control:,} | {test_treatment:,} |

Feature columns: {features}

Excluded from features: treatment, conversion, spend, user identifier, and synthetic true uplift.

## Test-set uplift ranking

Bin 1 contains the highest oracle uplift scores.

| Bin | Rows | Mean oracle score | Treated conversion | Control conversion | Observed uplift |
| ---: | ---: | ---: | ---: | ---: | ---: |
{ranking_rows}

## Curve metrics

- AUUC-style area: {auuc:.6f}
- Qini-style coefficient: {qini_value:.6f}
- Maximum Qini gain: {max_qini_row["qini_gain"]:.6f} at {max_qini_row["population_fraction"]:.1%} targeted

The cumulative uplift curve uses inverse-propensity contributions. The Qini-style curve subtracts
the straight-line random-targeting baseline; both areas use trapezoidal integration.

## Top-k targeting

| Targeted | Users | Treated | Control | Estimated uplift | Incremental conversions |
| ---: | ---: | ---: | ---: | ---: | ---: |
{policy_rows}

## Interpretation

The oracle score ranks users by the known treatment effect used to generate this synthetic data.
These results validate the split, ranking, curve, and policy calculations under controlled ground
truth. They establish an evaluation baseline only; no uplift model has been trained or evaluated.
"""


def generate_uplift_evaluation_report(
    data: pd.DataFrame,
    output_path: Path | str,
    test_size: float = 0.3,
    seed: int = 42,
    n_bins: int = 10,
) -> Path:
    """Write the synthetic oracle uplift evaluation report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = render_uplift_evaluation_report(
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
    """Read synthetic data and write its oracle evaluation report."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    report_path = generate_uplift_evaluation_report(
        data,
        options.output,
        test_size=options.test_size,
        seed=options.seed,
        n_bins=options.bins,
    )
    print(f"Wrote uplift evaluation report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
