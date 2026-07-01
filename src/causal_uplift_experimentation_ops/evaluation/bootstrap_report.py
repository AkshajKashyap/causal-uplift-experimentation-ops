"""Generate bootstrap uncertainty reporting for the logistic T-learner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.bootstrap import (
    BootstrapSummary,
    bootstrap_uplift_metrics,
    summarize_bootstrap_results,
)
from causal_uplift_experimentation_ops.evaluation.metrics import (
    auuc_score,
    qini_coefficient,
    qini_curve,
    top_k_policy_summary,
)
from causal_uplift_experimentation_ops.evaluation.splitting import split_experiment_data
from causal_uplift_experimentation_ops.models.t_learner import LogisticTLearner

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/t_learner_bootstrap_uncertainty.md")

METRIC_LABELS = {
    "auuc": "AUUC-style area",
    "qini_coefficient": "Qini-style coefficient",
    "maximum_qini_gain": "Maximum Qini gain",
    "top_10_percent_uplift": "Top 10% estimated uplift",
    "top_20_percent_uplift": "Top 20% estimated uplift",
    "top_30_percent_uplift": "Top 30% estimated uplift",
}


def _interpret(summary: BootstrapSummary) -> str:
    qini = summary.metric_statistics.set_index("metric").loc["qini_coefficient"]
    if qini["2.5%"] > 0 and summary.positive_qini_rate >= 0.95:
        conclusion = (
            "The held-out uplift ranking appears statistically stable under this bootstrap: "
            "the Qini interval remains above zero."
        )
    elif qini["97.5%"] < 0:
        conclusion = (
            "The held-out uplift ranking appears consistently worse than random targeting under "
            "this bootstrap."
        )
    else:
        conclusion = (
            "The held-out uplift signal remains statistically uncertain because the bootstrap "
            "Qini interval includes zero."
        )
    return (
        f"{conclusion} These percentile intervals condition on one fitted model and one test "
        "split; they do not include training-set or split-selection uncertainty."
    )


def _base_metrics(predictions: pd.DataFrame) -> dict[str, float]:
    qini = qini_curve(predictions)
    policies = top_k_policy_summary(predictions).set_index("target_fraction")
    return {
        "auuc": auuc_score(predictions),
        "qini_coefficient": qini_coefficient(predictions),
        "maximum_qini_gain": float(qini["qini_gain"].max()),
        "top_10_percent_uplift": float(policies.loc[0.1, "estimated_uplift"]),
        "top_20_percent_uplift": float(policies.loc[0.2, "estimated_uplift"]),
        "top_30_percent_uplift": float(policies.loc[0.3, "estimated_uplift"]),
    }


def render_bootstrap_report(
    data: pd.DataFrame,
    n_bootstrap: int = 100,
    bootstrap_seed: int = 42,
    split_seed: int = 42,
    test_size: float = 0.3,
) -> str:
    """Fit once, bootstrap held-out predictions, and render uncertainty."""
    split = split_experiment_data(data, test_size=test_size, seed=split_seed)
    model = LogisticTLearner(split.feature_columns, seed=split_seed).fit(split.train)
    predictions = model.predict(split.test)
    base = _base_metrics(predictions)
    bootstrap_results = bootstrap_uplift_metrics(
        predictions,
        n_bootstrap=n_bootstrap,
        seed=bootstrap_seed,
    )
    summary = summarize_bootstrap_results(bootstrap_results)
    statistics = summary.metric_statistics.set_index("metric")
    auuc_interval = statistics.loc["auuc"]
    qini_interval = statistics.loc["qini_coefficient"]

    base_rows = "\n".join(
        f"| {METRIC_LABELS[metric]} | {value:.6f} |" for metric, value in base.items()
    )
    summary_rows = "\n".join(
        "| {metric} | {mean:.6f} | {std:.6f} | {low:.6f} | {median:.6f} | "
        "{high:.6f} |".format(
            metric=METRIC_LABELS[row["metric"]],
            mean=row["mean"],
            std=row["std"],
            low=row["2.5%"],
            median=row["50%"],
            high=row["97.5%"],
        )
        for _, row in summary.metric_statistics.iterrows()
    )

    return f"""# T-Learner Bootstrap Uncertainty

## Scope

This report fits the existing logistic T-learner once, then performs a treatment-stratified row
bootstrap on its fixed held-out prediction set. It measures evaluation-sample uncertainty, not
training or split-selection uncertainty.

- Dataset rows: {len(data):,}
- Train rows: {len(split.train):,}
- Test rows: {len(split.test):,}
- Split seed: {split_seed}
- Bootstrap samples: {summary.sample_count:,}
- Bootstrap seed: {bootstrap_seed}

## Base held-out metrics

| Metric | Value |
| --- | ---: |
{base_rows}

## Bootstrap summary

| Metric | Mean | Std | 2.5% | 50% | 97.5% |
| --- | ---: | ---: | ---: | ---: | ---: |
{summary_rows}

## Approximate 95% percentile intervals

- AUUC-style area: [{auuc_interval["2.5%"]:.6f}, {auuc_interval["97.5%"]:.6f}]
- Qini-style coefficient: [{qini_interval["2.5%"]:.6f}, {qini_interval["97.5%"]:.6f}]
- Positive Qini samples: {summary.positive_qini_samples} of {summary.sample_count}
- Positive Qini rate: {summary.positive_qini_rate:.1%}

## Interpretation

{_interpret(summary)}
"""


def generate_bootstrap_report(
    data: pd.DataFrame,
    output_path: Path | str,
    n_bootstrap: int = 100,
    bootstrap_seed: int = 42,
    split_seed: int = 42,
    test_size: float = 0.3,
) -> Path:
    """Write the T-learner bootstrap uncertainty report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_bootstrap_report(
            data,
            n_bootstrap=n_bootstrap,
            bootstrap_seed=bootstrap_seed,
            split_seed=split_seed,
            test_size=test_size,
        ),
        encoding="utf-8",
    )
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--split-seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.3)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read synthetic data and write bootstrap uncertainty results."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    report_path = generate_bootstrap_report(
        data,
        options.output,
        n_bootstrap=options.n_bootstrap,
        bootstrap_seed=options.bootstrap_seed,
        split_seed=options.split_seed,
        test_size=options.test_size,
    )
    print(f"Wrote T-learner bootstrap report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
