"""Generate repeated-split robustness reporting for the logistic T-learner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.robustness import (
    DEFAULT_ROBUSTNESS_SEEDS,
    RobustnessSummary,
    evaluate_t_learner_repeated_splits,
    summarize_repeated_split_results,
)

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/t_learner_repeated_split_robustness.md")

METRIC_LABELS = {
    "auuc": "AUUC-style area",
    "qini_coefficient": "Qini-style coefficient",
    "maximum_qini_gain": "Maximum Qini gain",
    "top_10_percent_uplift": "Top 10% estimated uplift",
    "top_20_percent_uplift": "Top 20% estimated uplift",
    "top_30_percent_uplift": "Top 30% estimated uplift",
}


def _interpret(summary: RobustnessSummary) -> str:
    qini_row = summary.metric_statistics.set_index("metric").loc["qini_coefficient"]
    if summary.positive_qini_rate >= 0.8 and qini_row["mean"] > 0:
        direction = (
            "The T-learner appears directionally stable: most repeated splits beat the "
            "random-targeting baseline."
        )
    elif summary.positive_qini_rate <= 0.4:
        direction = (
            "The T-learner does not appear stable: most repeated splits fail to beat the "
            "random-targeting baseline."
        )
    else:
        direction = (
            "The T-learner appears split-sensitive: results are mixed around the "
            "random-targeting baseline."
        )

    if qini_row["std"] > abs(qini_row["mean"]):
        variability = "Qini variability exceeds its mean, so effect magnitude is notably noisy."
    else:
        variability = "Qini variability is smaller than its mean, suggesting moderate consistency."
    return (
        f"{direction} {variability} This is a finite repeated-split diagnostic, not a confidence "
        "interval or proof of out-of-sample policy value."
    )


def render_robustness_report(
    data: pd.DataFrame,
    seeds: Sequence[int] = DEFAULT_ROBUSTNESS_SEEDS,
    test_size: float = 0.3,
) -> str:
    """Run repeated splits and render their metric dispersion as Markdown."""
    results = evaluate_t_learner_repeated_splits(data, seeds=seeds, test_size=test_size)
    summary = summarize_repeated_split_results(results)
    seed_text = ", ".join(str(seed) for seed in results["seed"])

    result_rows = "\n".join(
        "| {seed:.0f} | {train:.0f} | {test:.0f} | {auuc:.6f} | {qini:.6f} | "
        "{max_qini:.6f} | {top_10:+.2%} | {top_20:+.2%} | {top_30:+.2%} |".format(
            seed=row.seed,
            train=row.train_rows,
            test=row.test_rows,
            auuc=row.auuc,
            qini=row.qini_coefficient,
            max_qini=row.maximum_qini_gain,
            top_10=row.top_10_percent_uplift,
            top_20=row.top_20_percent_uplift,
            top_30=row.top_30_percent_uplift,
        )
        for row in results.itertuples(index=False)
    )
    summary_rows = "\n".join(
        "| {metric} | {mean:.6f} | {std:.6f} | {min:.6f} | {max:.6f} |".format(
            metric=METRIC_LABELS[row.metric],
            mean=row.mean,
            std=row.std,
            min=row.min,
            max=row.max,
        )
        for row in summary.metric_statistics.itertuples(index=False)
    )

    return f"""# T-Learner Repeated-Split Robustness

## Scope

This report refits the existing logistic T-learner across deterministic, treatment-stratified
train/test splits. No new model family or hyperparameter tuning is introduced.

- Dataset rows: {len(data):,}
- Test fraction per run: {test_size:.0%}
- Seeds: {seed_text}

## Per-seed metrics

| Seed | Train rows | Test rows | AUUC | Qini coefficient | Max Qini gain | Top 10% uplift | Top 20% uplift | Top 30% uplift |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{result_rows}

## Summary statistics

Population standard deviation is calculated across the requested seed set.

| Metric | Mean | Std | Min | Max |
| --- | ---: | ---: | ---: | ---: |
{summary_rows}

- Positive Qini runs: {summary.positive_qini_runs} of {summary.run_count}
- Positive Qini rate: {summary.positive_qini_rate:.1%}

## Interpretation

{_interpret(summary)}
"""


def generate_robustness_report(
    data: pd.DataFrame,
    output_path: Path | str,
    seeds: Sequence[int] = DEFAULT_ROBUSTNESS_SEEDS,
    test_size: float = 0.3,
) -> Path:
    """Write the repeated-split T-learner robustness report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_robustness_report(data, seeds=seeds, test_size=test_size),
        encoding="utf-8",
    )
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_ROBUSTNESS_SEEDS))
    parser.add_argument("--test-size", type=float, default=0.3)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read synthetic data and write repeated-split robustness results."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    report_path = generate_robustness_report(
        data,
        options.output,
        seeds=options.seeds,
        test_size=options.test_size,
    )
    print(f"Wrote T-learner robustness report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
