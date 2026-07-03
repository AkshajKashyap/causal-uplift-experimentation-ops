"""Generate an offline targeting-policy value simulation report."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.comparison import DEFAULT_MODEL_NAMES
from causal_uplift_experimentation_ops.policy.comparison import (
    ModelPolicyComparisonResult,
    compare_model_policies,
)
from causal_uplift_experimentation_ops.policy.simulation import LEARNED_POLICY_NAMES
from causal_uplift_experimentation_ops.policy.value import PolicyValueConfig

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/targeting_policy_simulation.md")

MODEL_LABELS = {
    "logistic_t_learner": "Logistic T-learner",
    "logistic_s_learner": "Logistic S-learner",
    "random_forest_t_learner": "Random-forest T-learner",
    "random_baseline": "Random baseline",
    "oracle_baseline": "Synthetic oracle",
}

POLICY_LABELS = {
    "top_10_percent": "Top 10%",
    "top_20_percent": "Top 20%",
    "top_30_percent": "Top 30%",
    "positive_uplift": "All positive uplift",
    "random_matched_20_percent": "Random matched to 20%",
    "oracle_matched_20_percent": "Oracle matched to 20%",
}


def _best_row(frame: pd.DataFrame, metric: str) -> pd.Series:
    finite = frame[frame[metric].notna()]
    return finite.loc[finite[metric].idxmax()]


def _interpret(result: ModelPolicyComparisonResult) -> str:
    table = result.comparison
    learned = table[
        table["model"].isin(DEFAULT_MODEL_NAMES)
        & table["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    best_net = _best_row(learned, "net_value")
    random_best = _best_row(table[table["model"] == "random_baseline"], "net_value")
    oracle_best = _best_row(table[table["model"] == "oracle_baseline"], "net_value")

    depth_rows = learned[
        (learned["model"] == best_net["model"])
        & learned["policy_name"].isin(
            {"top_10_percent", "top_20_percent", "top_30_percent"}
        )
    ]
    top_30_roi = float(
        depth_rows.loc[depth_rows["policy_name"] == "top_30_percent", "roi"].iloc[0]
    )
    shallower_best_roi = float(
        depth_rows[
            depth_rows["policy_name"].isin({"top_10_percent", "top_20_percent"})
        ]["roi"].max()
    )
    depth_text = (
        "For the best-net model, targeting 30% reduces ROI versus the better shallower depth."
        if top_30_roi < shallower_best_roi
        else "For the best-net model, the 30% depth does not reduce ROI versus shallower depths."
    )
    return (
        f"{MODEL_LABELS[best_net['model']]} with {POLICY_LABELS[best_net['policy_name']]} "
        f"has the highest learned-policy net value. The best learned net value differs from "
        f"the random-score benchmark by ${best_net['net_value'] - random_best['net_value']:+,.2f} "
        f"and from the synthetic oracle by "
        f"${best_net['net_value'] - oracle_best['net_value']:+,.2f}. {depth_text} Treatment "
        "cost makes deeper targeting less attractive when marginal incremental conversion falls; "
        "uplift ranking matters only when it produces enough incremental value to cover that cost. "
        "The oracle is synthetic-only, and this remains an offline randomized-data simulation—not "
        "proof of production impact."
    )


def render_policy_report(
    data: pd.DataFrame,
    config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    seed: int = 42,
) -> str:
    """Cross-fit models, simulate policies, and render business value."""
    result = compare_model_policies(
        data,
        config=config,
        n_splits=n_splits,
        seed=seed,
    )
    assumptions = result.config
    table = result.comparison
    learned = table[
        table["model"].isin(DEFAULT_MODEL_NAMES)
        & table["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    best_net = _best_row(learned, "net_value")
    best_roi = _best_row(learned, "roi")
    model_names = ", ".join(MODEL_LABELS[name] for name in result.scored_predictions)
    policy_names = ", ".join(POLICY_LABELS[name] for name in table["policy_name"].unique())

    comparison_rows = "\n".join(
        "| {model} | {policy} | {users:,} | {fraction:.1%} | {predicted:+.2%} | "
        "{observed:+.2%} | {incremental:+.2f} | ${gross:+,.2f} | ${cost:,.2f} | "
        "${net:+,.2f} | {roi:+.2f} |".format(
            model=MODEL_LABELS[row.model],
            policy=POLICY_LABELS[row.policy_name],
            users=row.selected_users,
            fraction=row.selected_fraction,
            predicted=row.mean_predicted_uplift,
            observed=row.observed_uplift,
            incremental=row.estimated_incremental_conversions,
            gross=row.gross_value,
            cost=row.treatment_cost,
            net=row.net_value,
            roi=row.roi,
        )
        for row in table.itertuples(index=False)
    )
    best_by_model = (
        table.loc[table.groupby("model")["net_value"].idxmax()]
        .sort_values("net_value", ascending=False)
        .reset_index(drop=True)
    )
    best_rows = "\n".join(
        "| {model} | {policy} | ${net:+,.2f} | {roi:+.2f} |".format(
            model=MODEL_LABELS[row.model],
            policy=POLICY_LABELS[row.policy_name],
            net=row.net_value,
            roi=row.roi,
        )
        for row in best_by_model.itertuples(index=False)
    )

    return f"""# Targeting Policy Simulation

## Scope and assumptions

Cross-fitted predictions are converted into offline targeting decisions. Incremental conversions
use the randomized treatment-minus-control conversion difference within selected users.

- Dataset rows: {len(data):,}
- Cross-fitting folds: {n_splits}
- Value per conversion: ${assumptions.value_per_conversion:,.2f}
- Treatment cost per user: ${assumptions.treatment_cost_per_user:,.2f}
- Budget: {f"${assumptions.budget:,.2f}" if assumptions.budget is not None else "None"}
- Capacity fraction: {f"{assumptions.capacity_fraction:.1%}" if assumptions.capacity_fraction is not None else "None"}
- Minimum predicted uplift: {f"{assumptions.min_predicted_uplift:.2%}" if assumptions.min_predicted_uplift is not None else "None"}
- Models evaluated: {model_names}
- Policies evaluated: {policy_names}

## Model-policy comparison

| Model | Policy | Users | Fraction | Mean predicted uplift | Observed uplift | Incremental conversions | Gross value | Cost | Net value | ROI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{comparison_rows}

## Best policy by model

| Model | Best net-value policy | Net value | ROI |
| --- | --- | ---: | ---: |
{best_rows}

- Best learned pair by net value: **{MODEL_LABELS[best_net["model"]]} — {POLICY_LABELS[best_net["policy_name"]]}** (${best_net["net_value"]:+,.2f})
- Best learned pair by ROI: **{MODEL_LABELS[best_roi["model"]]} — {POLICY_LABELS[best_roi["policy_name"]]}** ({best_roi["roi"]:+.2f})

## Interpretation

{_interpret(result)}
"""


def generate_policy_report(
    data: pd.DataFrame,
    output_path: Path | str,
    config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    seed: int = 42,
) -> Path:
    """Write the cross-fitted targeting-policy simulation report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_policy_report(data, config=config, n_splits=n_splits, seed=seed),
        encoding="utf-8",
    )
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--value-per-conversion", type=float, default=100.0)
    parser.add_argument("--treatment-cost", type=float, default=1.0)
    parser.add_argument("--budget", type=float)
    parser.add_argument("--capacity-fraction", type=float)
    parser.add_argument("--min-predicted-uplift", type=float)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read experiment data and write the targeting-policy report."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    config = PolicyValueConfig(
        value_per_conversion=options.value_per_conversion,
        treatment_cost_per_user=options.treatment_cost,
        budget=options.budget,
        capacity_fraction=options.capacity_fraction,
        min_predicted_uplift=options.min_predicted_uplift,
    )
    report_path = generate_policy_report(
        data,
        options.output,
        config=config,
        n_splits=options.folds,
        seed=options.seed,
    )
    print(f"Wrote targeting-policy report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
