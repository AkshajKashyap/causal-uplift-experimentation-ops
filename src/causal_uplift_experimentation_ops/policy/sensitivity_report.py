"""Generate policy sensitivity and decision uncertainty reporting."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.comparison import DEFAULT_MODEL_NAMES
from causal_uplift_experimentation_ops.policy.sensitivity import (
    PolicySensitivityResult,
    analyze_policy_sensitivity,
)
from causal_uplift_experimentation_ops.policy.simulation import LEARNED_POLICY_NAMES
from causal_uplift_experimentation_ops.policy.value import PolicyValueConfig

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/policy_sensitivity_analysis.md")

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

ASSUMPTION_LABELS = {
    "value_per_conversion": "Value / conversion",
    "treatment_cost_per_user": "Treatment cost / user",
    "capacity_fraction": "Capacity fraction",
    "budget": "Budget",
}


def _best_learned_base(result: PolicySensitivityResult) -> pd.Series:
    learned = result.base_comparison[
        result.base_comparison["model"].isin(DEFAULT_MODEL_NAMES)
        & result.base_comparison["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    return learned.loc[learned["net_value"].idxmax()]


def _format_assumption_value(name: str, value: float) -> str:
    if name in {"value_per_conversion", "treatment_cost_per_user", "budget"}:
        return f"${value:,.2f}"
    return f"{value:.0%}"


def _scenario_rows(frame: pd.DataFrame, assumption_columns: list[str]) -> str:
    rows = []
    for row in frame.to_dict(orient="records"):
        assumptions = " × ".join(
            f"{ASSUMPTION_LABELS[name]}={_format_assumption_value(name, row[name])}"
            for name in assumption_columns
        )
        rows.append(
            "| {assumptions} | {model} | {policy} | {users:,} | ${net:+,.2f} | "
            "{roi:+.2f} | ${random_diff:+,.2f} | {oracle_ratio:.1%} | {changed} |".format(
                assumptions=assumptions,
                model=MODEL_LABELS[row["best_net_model"]],
                policy=POLICY_LABELS[row["best_net_policy"]],
                users=row["best_net_selected_users"],
                net=row["best_net_value"],
                roi=row["best_roi"],
                random_diff=row["learned_random_net_difference"],
                oracle_ratio=row["learned_oracle_net_ratio"],
                changed="Yes" if row["recommendation_changed"] else "No",
            )
        )
    return "\n".join(rows)


def _interpret(result: PolicySensitivityResult) -> str:
    stability = result.stability
    assumption_ranges = (
        result.one_way.groupby("assumption")["best_net_value"]
        .agg(lambda values: values.max() - values.min())
        .sort_values(ascending=False)
    )
    most_influential = ASSUMPTION_LABELS[str(assumption_ranges.index[0])]
    robust = (
        stability.same_model_win_rate >= 0.6
        and stability.same_policy_win_rate >= 0.6
        and stability.positive_learned_net_value_rate >= 0.9
    )
    stability_text = (
        "The recommendation is reasonably robust across the tested scenarios."
        if robust
        else "The recommendation is fragile across the tested scenarios."
    )
    return (
        f"{stability_text} {most_influential} creates the largest one-way swing in best learned "
        f"net value. The base policy breaks even near a treatment cost of "
        f"${result.break_even.maximum_treatment_cost:,.2f} per user, so sufficiently high costs "
        "can erase apparent value. Target-all outcomes largely reproduce the overall A/B effect "
        "and are not evidence of superior ranking; constrained depths are more informative about "
        "who should be treated. Oracle comparisons use unavailable synthetic truth, and every "
        "result remains an offline simulation rather than production proof."
    )


def render_sensitivity_report(
    data: pd.DataFrame,
    base_config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    seed: int = 42,
) -> str:
    """Run default sensitivity analysis and render all decision diagnostics."""
    result = analyze_policy_sensitivity(
        data,
        base_config=base_config,
        n_splits=n_splits,
        seed=seed,
    )
    assumptions = result.base_config
    base_best = _best_learned_base(result)
    stability = result.stability
    stable_model, stable_policy = stability.most_frequent_model_policy.split(" / ")

    one_way_rows = "\n".join(
        "| {assumption} | {value} | {model} | {policy} | {users:,} | ${net:+,.2f} | "
        "{roi:+.2f} | ${random_diff:+,.2f} | {oracle_ratio:.1%} | {changed} |".format(
            assumption=ASSUMPTION_LABELS[row.assumption],
            value=_format_assumption_value(row.assumption, row.assumption_value),
            model=MODEL_LABELS[row.best_net_model],
            policy=POLICY_LABELS[row.best_net_policy],
            users=row.best_net_selected_users,
            net=row.best_net_value,
            roi=row.best_roi,
            random_diff=row.learned_random_net_difference,
            oracle_ratio=row.learned_oracle_net_ratio,
            changed="Yes" if row.recommendation_changed else "No",
        )
        for row in result.one_way.itertuples(index=False)
    )
    value_cost_rows = _scenario_rows(
        result.value_cost_grid,
        ["value_per_conversion", "treatment_cost_per_user"],
    )
    capacity_cost_rows = _scenario_rows(
        result.capacity_cost_grid,
        ["capacity_fraction", "treatment_cost_per_user"],
    )
    break_even_rows = "\n".join(
        "| {policy} | {users:,} | {incremental:+.2f} | ${cost:,.2f} | {profitable} |".format(
            policy=POLICY_LABELS[row.policy_name],
            users=row.selected_users,
            incremental=row.estimated_incremental_conversions,
            cost=row.break_even_treatment_cost,
            profitable="Yes" if row.profitable_at_base_cost else "No",
        )
        for row in result.break_even.policy_thresholds.itertuples(index=False)
    )

    return f"""# Policy Sensitivity Analysis

## Scope and base assumptions

Cross-fitted model scores are held fixed while economic and operational assumptions vary.

- Dataset rows: {len(data):,}
- Models evaluated: {", ".join(MODEL_LABELS[name] for name in result.scored_predictions)}
- Value per conversion: ${assumptions.value_per_conversion:,.2f}
- Treatment cost per user: ${assumptions.treatment_cost_per_user:,.2f}
- Base budget: {f"${assumptions.budget:,.2f}" if assumptions.budget is not None else "None"}
- Base capacity: {f"{assumptions.capacity_fraction:.1%}" if assumptions.capacity_fraction is not None else "None"}
- Base best learned pair: **{MODEL_LABELS[base_best["model"]]} — {POLICY_LABELS[base_best["policy_name"]]}**

## One-way sensitivity

| Assumption | Value | Best model | Best policy | Users | Net value | Best ROI | Learned vs random | Learned / oracle | Changed? |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
{one_way_rows}

## Value per conversion × treatment cost

| Scenario | Best model | Best policy | Users | Net value | Best ROI | Learned vs random | Learned / oracle | Changed? |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
{value_cost_rows}

## Capacity × treatment cost

| Scenario | Best model | Best policy | Users | Net value | Best ROI | Learned vs random | Learned / oracle | Changed? |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
{capacity_cost_rows}

## Decision stability

| Measure | Value |
| --- | ---: |
| Scenarios | {stability.scenario_count} |
| Most frequent best model | {MODEL_LABELS[stability.most_frequent_best_model]} |
| Most frequent best policy | {POLICY_LABELS[stability.most_frequent_best_policy]} |
| Most stable pair | {MODEL_LABELS[stable_model]} / {POLICY_LABELS[stable_policy]} |
| Same-model win rate | {stability.same_model_win_rate:.1%} |
| Same-policy win rate | {stability.same_policy_win_rate:.1%} |
| Learned beats random rate | {stability.learned_beats_random_rate:.1%} |
| Positive learned net-value rate | {stability.positive_learned_net_value_rate:.1%} |
| Average learned / oracle ratio | {stability.average_learned_oracle_ratio:.1%} |
| Worst-case learned net value | ${stability.worst_case_learned_net_value:+,.2f} |
| Worst-case best ROI | {stability.worst_case_roi:+.2f} |
| Best-case learned net value | ${stability.best_case_learned_net_value:+,.2f} |
| Best-case ROI | {stability.best_case_roi:+.2f} |

## Break-even analysis

- Base best model-policy: **{MODEL_LABELS[result.break_even.model]} — {POLICY_LABELS[result.break_even.policy_name]}**
- Maximum treatment cost with positive net value: **${result.break_even.maximum_treatment_cost:,.2f} per user**
- Minimum value per conversion with positive net value: **${result.break_even.minimum_value_per_conversion:,.2f}**

| Policy | Users | Incremental conversions | Break-even cost / user | Profitable at base cost? |
| --- | ---: | ---: | ---: | :---: |
{break_even_rows}

## Interpretation

{_interpret(result)}
"""


def generate_sensitivity_report(
    data: pd.DataFrame,
    output_path: Path | str,
    base_config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    seed: int = 42,
) -> Path:
    """Write the policy sensitivity analysis report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_sensitivity_report(
            data,
            base_config=base_config,
            n_splits=n_splits,
            seed=seed,
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
    parser.add_argument("--value-per-conversion", type=float, default=100.0)
    parser.add_argument("--treatment-cost", type=float, default=1.0)
    parser.add_argument("--budget", type=float)
    parser.add_argument("--capacity-fraction", type=float)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read experiment data and write policy sensitivity results."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    config = PolicyValueConfig(
        value_per_conversion=options.value_per_conversion,
        treatment_cost_per_user=options.treatment_cost,
        budget=options.budget,
        capacity_fraction=options.capacity_fraction,
    )
    report_path = generate_sensitivity_report(
        data,
        options.output,
        base_config=config,
        n_splits=options.folds,
        seed=options.seed,
    )
    print(f"Wrote policy sensitivity report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
