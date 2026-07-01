"""Create a Markdown report for the baseline synthetic A/B experiment."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.experiments.analysis import (
    ExperimentSummary,
    numeric_covariate_balance,
    summarize_experiment,
)

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/synthetic_ab_summary.md")


def _format_relative_lift(value: float) -> str:
    return "undefined (zero control rate)" if pd.isna(value) else f"{value:.2%}"


def _format_percentage_points(value: float) -> str:
    return f"{value * 100:+.2f} pp"


def _format_signed_currency(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    return f"{sign}${abs(value):,.2f}"


def _interpret(summary: ExperimentSummary, max_balance_difference: float) -> str:
    direction = "increased" if summary.conversion_treatment_effect >= 0 else "decreased"
    significance = (
        "The two-sided p-value is below 0.05, providing evidence of a difference "
        "in conversion rates."
        if summary.conversion_p_value < 0.05
        else "The two-sided p-value is not below 0.05, so this experiment does not provide "
        "strong evidence of a conversion-rate difference."
    )
    balance = (
        "All checked numeric covariates are within the 0.10 absolute standardized-difference "
        "threshold."
        if max_balance_difference <= 0.1
        else "At least one numeric covariate exceeds the 0.10 absolute standardized-difference "
        "threshold and should be reviewed."
    )
    return (
        f"Observed conversion {direction} under treatment by "
        f"{abs(summary.conversion_treatment_effect) * 100:.2f} percentage points. "
        f"{significance} {balance} "
        "These estimates describe the average effect in this randomized A/B experiment; "
        "they do not estimate individual uplift."
    )


def render_ab_report(data: pd.DataFrame) -> str:
    """Render baseline experiment statistics as Markdown."""
    summary = summarize_experiment(data)
    balance = numeric_covariate_balance(data)
    max_balance_difference = float(balance["absolute_standardized_mean_difference"].max())

    balance_rows = "\n".join(
        "| {covariate} | {control_mean:.3f} | {treatment_mean:.3f} | {smd:.3f} | {status} |".format(
            covariate=row.covariate,
            control_mean=row.control_mean,
            treatment_mean=row.treatment_mean,
            smd=row.standardized_mean_difference,
            status="Yes" if row.balanced else "No",
        )
        for row in balance.itertuples(index=False)
    )

    return f"""# Synthetic A/B Experiment Summary

## Scope

This report compares a randomized binary treatment against control. Conversion is binary and
spend is numeric. Estimates apply to this randomized experiment and do not imply individual
treatment effects.

## Sample

| Metric | Control | Treatment | Total |
| --- | ---: | ---: | ---: |
| Users | {summary.control_count:,} | {summary.treatment_count:,} | {summary.row_count:,} |

## Outcomes

| Metric | Control | Treatment | Difference |
| --- | ---: | ---: | ---: |
| Conversion rate | {summary.control_conversion_rate:.2%} | {summary.treatment_conversion_rate:.2%} | {_format_percentage_points(summary.conversion_treatment_effect)} |
| Average spend | ${summary.control_average_spend:,.2f} | ${summary.treatment_average_spend:,.2f} | {_format_signed_currency(summary.spend_treatment_effect)} |

- Relative conversion lift: {_format_relative_lift(summary.conversion_relative_lift)}
- 95% confidence interval for conversion-rate difference: [{_format_percentage_points(summary.conversion_ci_lower)}, {_format_percentage_points(summary.conversion_ci_upper)}]
- Two-sided p-value for conversion-rate difference: {summary.conversion_p_value:.4g}

## Numeric covariate balance

Absolute standardized mean differences at or below 0.10 are marked balanced.

| Covariate | Control mean | Treatment mean | Standardized difference | Balanced |
| --- | ---: | ---: | ---: | :---: |
{balance_rows}

## Interpretation

{_interpret(summary, max_balance_difference)}
"""


def generate_ab_report(data: pd.DataFrame, output_path: Path | str) -> Path:
    """Write a Markdown A/B report and return its path."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_ab_report(data), encoding="utf-8")
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"Experiment CSV path (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Markdown report path (default: {DEFAULT_REPORT_PATH})",
    )
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read, validate, and summarize an experiment CSV."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    report_path = generate_ab_report(data, options.output)
    print(f"Wrote A/B report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
