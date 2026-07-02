"""Generate a cross-fitted uplift model comparison report."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.comparison import (
    DEFAULT_MODEL_NAMES,
    ModelComparisonResult,
    compare_uplift_models,
)

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/crossfit_model_comparison.md")

MODEL_LABELS = {
    "logistic_t_learner": "Logistic T-learner",
    "logistic_s_learner": "Logistic S-learner",
    "random_forest_t_learner": "Random-forest T-learner",
    "random_baseline": "Random baseline",
    "oracle_baseline": "Synthetic oracle",
}


def _interpret(result: ModelComparisonResult) -> str:
    learned = result.comparison[result.comparison["model"].isin(DEFAULT_MODEL_NAMES)]
    best = learned.sort_values("qini_coefficient", ascending=False).iloc[0]
    uncertainty = result.uncertainty.set_index("model").loc[best["model"]]
    random_qini = float(
        result.comparison.set_index("model").loc["random_baseline", "qini_coefficient"]
    )
    beats_random = best["qini_coefficient"] > random_qini
    random_text = (
        "beats the realized random-score baseline"
        if beats_random
        else "does not beat the realized random-score baseline"
    )
    interval_text = (
        "Its bootstrap Qini interval excludes zero."
        if uncertainty["qini_lower"] > 0
        else "Its bootstrap Qini interval includes zero, so ranking uncertainty remains."
    )

    oracle_text = ""
    if "oracle_baseline" in set(result.comparison["model"]):
        oracle_qini = float(
            result.comparison.set_index("model").loc["oracle_baseline", "qini_coefficient"]
        )
        difference = float(best["qini_coefficient"] - oracle_qini)
        oracle_text = (
            f" Its realized Qini difference from the synthetic oracle is {difference:+.6f}; "
            "finite-sample outcome noise means the oracle need not maximize every observed curve."
        )
    return (
        f"{MODEL_LABELS[best['model']]} has the strongest fitted-model Qini coefficient and "
        f"{random_text}. {interval_text}{oracle_text} The oracle exists only because synthetic "
        "true uplift is known. These randomized synthetic results validate the comparison "
        "framework, but do not prove causal lift in another real-world population."
    )


def render_comparison_report(
    data: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
    n_bootstrap: int = 100,
) -> str:
    """Run cross-fitted comparison and render its metrics as Markdown."""
    result = compare_uplift_models(
        data,
        n_splits=n_splits,
        seed=seed,
        n_bootstrap=n_bootstrap,
    )
    learned = result.comparison[result.comparison["model"].isin(DEFAULT_MODEL_NAMES)]
    best = learned.sort_values("qini_coefficient", ascending=False).iloc[0]
    features = ", ".join(f"`{column}`" for column in result.feature_columns)
    model_names = ", ".join(MODEL_LABELS[name] for name in result.scored_predictions)

    comparison_rows = "\n".join(
        "| {rank:.0f} | {model} | {auuc:.6f} | {qini:.6f} | {max_qini:.6f} | "
        "{top_10:+.2%} | {top_20:+.2%} | {top_30:+.2%} | {difference:+.6f} |".format(
            rank=row.qini_rank,
            model=MODEL_LABELS[row.model],
            auuc=row.auuc,
            qini=row.qini_coefficient,
            max_qini=row.maximum_qini_gain,
            top_10=row.top_10_percent_uplift,
            top_20=row.top_20_percent_uplift,
            top_30=row.top_30_percent_uplift,
            difference=row.qini_difference_vs_random,
        )
        for row in result.comparison.itertuples(index=False)
    )
    uncertainty_rows = "\n".join(
        "| {model} | {mean:.6f} | {lower:.6f} | {median:.6f} | {upper:.6f} | "
        "{positive:.1%} |".format(
            model=MODEL_LABELS[row.model],
            mean=row.qini_mean,
            lower=row.qini_lower,
            median=row.qini_median,
            upper=row.qini_upper,
            positive=row.positive_qini_rate,
        )
        for row in result.uncertainty.itertuples(index=False)
    )

    return f"""# Cross-Fitted Uplift Model Comparison

## Scope

Every fitted model receives one out-of-fold prediction per row from deterministic,
treatment-stratified {n_splits}-fold cross-fitting. Bootstrap intervals resample the resulting
out-of-fold scored rows within treatment arms.

- Dataset rows: {len(data):,}
- Cross-fitting folds: {n_splits}
- Bootstrap samples per model: {n_bootstrap}
- Models compared: {model_names}
- Leakage-safe features: {features}

## Model comparison

| Qini rank | Model | AUUC | Qini | Max Qini gain | Top 10% | Top 20% | Top 30% | Qini vs random |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{comparison_rows}

Best fitted model by Qini coefficient: **{MODEL_LABELS[best["model"]]}**

## Bootstrap Qini uncertainty

| Model | Mean | 2.5% | 50% | 97.5% | Positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
{uncertainty_rows}

## Interpretation

{_interpret(result)}
"""


def generate_comparison_report(
    data: pd.DataFrame,
    output_path: Path | str,
    n_splits: int = 5,
    seed: int = 42,
    n_bootstrap: int = 100,
) -> Path:
    """Write the cross-fitted model comparison report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_comparison_report(
            data,
            n_splits=n_splits,
            seed=seed,
            n_bootstrap=n_bootstrap,
        ),
        encoding="utf-8",
    )
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-bootstrap", type=int, default=100)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read synthetic data and write cross-fitted model comparison results."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    report_path = generate_comparison_report(
        data,
        options.output,
        n_splits=options.folds,
        seed=options.seed,
        n_bootstrap=options.n_bootstrap,
    )
    print(f"Wrote cross-fitted comparison report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
