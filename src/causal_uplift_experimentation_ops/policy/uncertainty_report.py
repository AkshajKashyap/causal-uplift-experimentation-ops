"""Generate policy value bootstrap uncertainty and regret reporting."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.policy.uncertainty import (
    DEFAULT_CHOSEN_POLICIES,
    PolicyUncertaintyResult,
    analyze_policy_uncertainty,
)
from causal_uplift_experimentation_ops.policy.value import PolicyValueConfig

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/policy_value_uncertainty.md")

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

CHOSEN_POLICY_ID = "logistic_s_learner__positive_uplift"


def _policy_label(row: pd.Series) -> str:
    return f"{MODEL_LABELS[row['model']]} / {POLICY_LABELS[row['policy_name']]}"


def _format_probability(value: float) -> str:
    return f"{value:.1%}" if np.isfinite(value) else "N/A"


def _interpret(result: PolicyUncertaintyResult) -> str:
    summary = result.summary.set_index("policy_id")
    chosen = summary.loc[CHOSEN_POLICY_ID]
    learned = result.summary[
        ~result.summary["model"].isin({"random_baseline", "oracle_baseline"})
    ]
    highest_positive = learned.loc[learned["probability_positive_net_value"].idxmax()]
    highest_best = learned.loc[learned["probability_bootstrap_best"].idxmax()]

    justified = (
        chosen["probability_positive_net_value"] >= 0.95
        and chosen["net_value_2_5"] > 0
        and chosen["probability_bootstrap_best"] >= 0.8
        and chosen["mean_net_value"] >= learned["mean_net_value"].max()
    )
    decision = (
        "Under these fixed base assumptions, the all-positive policy remains justified for "
        "maximizing total net value."
        if justified
        else "The all-positive policy is not decisively safer than the constrained alternatives."
    )
    random_comparison = (
        "Its probability of beating a matched random policy is "
        f"{_format_probability(chosen['probability_beats_random'])}."
        if np.isfinite(chosen["probability_beats_random"])
        else "A matched-random comparison is not meaningful because both policies treat every "
        "user; their values tie by construction."
    )
    return (
        f"{decision} Its probability of positive net value is "
        f"{chosen['probability_positive_net_value']:.1%}. {random_comparison} "
        f"{_policy_label(highest_positive)} has the highest positive-value probability, while "
        f"{_policy_label(highest_best)} is bootstrap-best most often. Constrained policies have "
        "higher ROI but lower total net value here. This conclusion remains fragile to the value, "
        "cost, and capacity assumptions explored in Milestone 9. Negative oracle regret can occur "
        "because realized randomized outcomes are noisy; true individual uplift is known only in "
        "this synthetic benchmark. Offline bootstrap uncertainty is not a substitute for a "
        "prospective production experiment."
    )


def render_uncertainty_report(
    data: pd.DataFrame,
    config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    n_bootstrap: int = 100,
    seed: int = 42,
) -> str:
    """Cross-fit models, bootstrap chosen policies, and render uncertainty."""
    result = analyze_policy_uncertainty(
        data,
        config=config,
        n_splits=n_splits,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    assumptions = result.config
    summary = result.summary
    chosen = summary.set_index("policy_id").loc[CHOSEN_POLICY_ID]
    policy_names = ", ".join(
        f"{MODEL_LABELS[policy.model]} / {POLICY_LABELS[policy.policy_name]}"
        for policy in DEFAULT_CHOSEN_POLICIES
    )

    value_rows = "\n".join(
        "| {policy} | ${mean:+,.2f} | ${std:,.2f} | ${low:+,.2f} | ${median:+,.2f} | "
        "${high:+,.2f} | {positive:.1%} |".format(
            policy=_policy_label(row),
            mean=row.mean_net_value,
            std=row.std_net_value,
            low=row.net_value_2_5,
            median=row.net_value_50,
            high=row.net_value_97_5,
            positive=row.probability_positive_net_value,
        )
        for _, row in summary.iterrows()
    )
    roi_rows = "\n".join(
        "| {policy} | {mean:+.2f} | {low:+.2f} | {median:+.2f} | {high:+.2f} | "
        "{positive:.1%} | {random} | {all_positive} |".format(
            policy=_policy_label(row),
            mean=row.mean_roi,
            low=row.roi_2_5,
            median=row.roi_50,
            high=row.roi_97_5,
            positive=row.probability_positive_roi,
            random=_format_probability(row.probability_beats_random),
            all_positive=_format_probability(row.probability_beats_all_positive),
        )
        for _, row in summary.iterrows()
    )
    learned = summary[
        ~summary["model"].isin({"random_baseline", "oracle_baseline"})
    ]
    regret_rows = "\n".join(
        "| {policy} | ${oracle_mean:+,.2f} | ${oracle_median:+,.2f} | "
        "[${oracle_low:+,.2f}, ${oracle_high:+,.2f}] | ${best_regret:,.2f} | "
        "{best_probability:.1%} | {random_probability} |".format(
            policy=_policy_label(row),
            oracle_mean=row.mean_oracle_regret,
            oracle_median=row.median_oracle_regret,
            oracle_low=row.oracle_regret_2_5,
            oracle_high=row.oracle_regret_97_5,
            best_regret=row.mean_bootstrap_best_regret,
            best_probability=row.probability_bootstrap_best,
            random_probability=_format_probability(row.probability_beats_random),
        )
        for _, row in learned.iterrows()
    )

    return f"""# Policy Value Bootstrap Uncertainty

## Scope and assumptions

Cross-fitted scores are held fixed. Each paired bootstrap replicate resamples randomized treatment
arms, then evaluates every chosen policy on the same sampled users.

- Dataset rows: {len(data):,}
- Cross-fitting folds: {n_splits}
- Bootstrap samples: {n_bootstrap}
- Value per conversion: ${assumptions.value_per_conversion:,.2f}
- Treatment cost per user: ${assumptions.treatment_cost_per_user:,.2f}
- Budget: {f"${assumptions.budget:,.2f}" if assumptions.budget is not None else "None"}
- Capacity: {f"{assumptions.capacity_fraction:.1%}" if assumptions.capacity_fraction is not None else "None"}
- Policies evaluated: {policy_names}, Random baseline / matched 20%, Synthetic oracle / matched 20%

## Policy net-value uncertainty

| Policy | Mean | Std | 2.5% | 50% | 97.5% | P(net > 0) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{value_rows}

## ROI uncertainty and paired comparisons

| Policy | Mean ROI | 2.5% | 50% | 97.5% | P(ROI > 0) | P(beats random) | P(beats all-positive) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{roi_rows}

## Regret summary for learned policies

| Policy | Mean oracle regret | Median oracle regret | Oracle regret 95% interval | Mean best-policy regret | P(bootstrap-best) | P(beats random) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{regret_rows}

## Chosen-policy result

- Policy: **Logistic S-learner / All positive uplift**
- Mean net value: **${chosen["mean_net_value"]:+,.2f}**
- Approximate 95% net-value interval: **[${chosen["net_value_2_5"]:+,.2f}, ${chosen["net_value_97_5"]:+,.2f}]**
- Probability of positive net value: **{chosen["probability_positive_net_value"]:.1%}**
- Probability of beating matched random: **{_format_probability(chosen["probability_beats_random"])}**
- Probability of being bootstrap-best: **{chosen["probability_bootstrap_best"]:.1%}**

## Interpretation

{_interpret(result)}
"""


def generate_uncertainty_report(
    data: pd.DataFrame,
    output_path: Path | str,
    config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    n_bootstrap: int = 100,
    seed: int = 42,
) -> Path:
    """Write the paired policy value uncertainty report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_uncertainty_report(
            data,
            config=config,
            n_splits=n_splits,
            n_bootstrap=n_bootstrap,
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
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--value-per-conversion", type=float, default=100.0)
    parser.add_argument("--treatment-cost", type=float, default=1.0)
    parser.add_argument("--budget", type=float)
    parser.add_argument("--capacity-fraction", type=float)
    parser.add_argument("--min-predicted-uplift", type=float)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read experiment data and write policy uncertainty results."""
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
    report_path = generate_uncertainty_report(
        data,
        options.output,
        config=config,
        n_splits=options.folds,
        n_bootstrap=options.n_bootstrap,
        seed=options.seed,
    )
    print(f"Wrote policy uncertainty report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
