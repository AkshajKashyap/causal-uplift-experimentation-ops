"""Generate a synthetic prospective randomized policy-trial report."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.evaluation.comparison import (
    score_comparison_models,
)
from causal_uplift_experimentation_ops.experiments.policy_trial import (
    GuardrailConfig,
    PolicyTrialConfig,
    PolicyTrialRun,
    run_policy_trial,
)

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_REPORT_PATH = Path("reports/prospective_policy_trial.md")

POLICY_LABELS = {
    "positive_uplift": "Logistic S-learner / All positive uplift",
    "top_20_percent": "Logistic S-learner / Top 20%",
}


def run_default_policy_trials(
    data: pd.DataFrame,
    *,
    n_splits: int = 5,
    seed: int = 42,
    treatment_cost_per_user: float = 1.0,
    value_per_conversion: float = 100.0,
    traffic_allocation: float = 1.0,
    holdout_fraction: float = 0.2,
    minimum_detectable_effect_target: float = 0.02,
    alpha: float = 0.05,
    power: float = 0.80,
    n_batches: int = 5,
    guardrails: GuardrailConfig | None = None,
) -> dict[str, PolicyTrialRun]:
    """Cross-fit once and simulate all-positive and top-20% randomized trials."""
    predictions, _ = score_comparison_models(data, n_splits=n_splits, seed=seed)
    scored = predictions["logistic_s_learner"]
    thresholds = guardrails or GuardrailConfig()
    runs: dict[str, PolicyTrialRun] = {}
    for offset, policy_rule in enumerate(("positive_uplift", "top_20_percent")):
        config = PolicyTrialConfig(
            policy_name=POLICY_LABELS[policy_rule],
            candidate_model_name="logistic_s_learner",
            candidate_policy_rule=policy_rule,
            treatment_cost_per_user=treatment_cost_per_user,
            value_per_conversion=value_per_conversion,
            traffic_allocation=traffic_allocation,
            holdout_fraction=holdout_fraction,
            randomization_seed=seed,
            minimum_detectable_effect_target=minimum_detectable_effect_target,
            alpha=alpha,
            power=power,
            n_batches=n_batches,
            guardrails=thresholds,
        )
        runs[policy_rule] = run_policy_trial(scored, config, outcome_seed=seed + 100 + offset)
    return runs


def _render_guardrails(runs: dict[str, PolicyTrialRun]) -> str:
    rows = []
    for policy_rule, run in runs.items():
        for guardrail in run.summary.guardrails.itertuples(index=False):
            rows.append(
                "| {policy} | {guardrail} | {observed:+.4f} | {threshold} | {status} |".format(
                    policy=POLICY_LABELS[policy_rule],
                    guardrail=guardrail.guardrail,
                    observed=guardrail.observed,
                    threshold=guardrail.threshold,
                    status=guardrail.status,
                )
            )
    return "\n".join(rows)


def _render_batches(runs: dict[str, PolicyTrialRun]) -> str:
    rows = []
    for policy_rule, run in runs.items():
        for batch in run.batch_results.itertuples(index=False):
            rows.append(
                "| {policy} | {batch} | {sample:,} | {treatment:,} | {holdout:,} | "
                "{lift:+.2%} | [{lower:+.2%}, {upper:+.2%}] | {p_value:.4f} | "
                "${net:+,.2f} | {roi:+.2f} | {status} |".format(
                    policy=POLICY_LABELS[policy_rule],
                    batch=batch.batch,
                    sample=batch.cumulative_sample_size,
                    treatment=batch.treatment_count,
                    holdout=batch.holdout_count,
                    lift=batch.conversion_lift,
                    lower=batch.confidence_interval_lower,
                    upper=batch.confidence_interval_upper,
                    p_value=batch.p_value,
                    net=batch.cumulative_net_value,
                    roi=batch.cumulative_roi,
                    status=batch.guardrail_status,
                )
            )
    return "\n".join(rows)


def _interpret(runs: dict[str, PolicyTrialRun]) -> str:
    best_net_rule = max(runs, key=lambda name: runs[name].summary.net_value)
    best_roi_rule = max(runs, key=lambda name: runs[name].summary.roi)
    best_net = runs[best_net_rule].summary
    best_roi = runs[best_roi_rule].summary
    significance = (
        "Its confidence interval excludes zero at the configured alpha."
        if best_net.confidence_interval_lower > 0
        else "Its confidence interval still includes zero, so the simulated evidence is not "
        "conclusive at the configured alpha."
    )
    return (
        f"{POLICY_LABELS[best_net_rule]} produces the higher simulated total net value "
        f"(${best_net.net_value:+,.2f}); {POLICY_LABELS[best_roi_rule]} produces the higher ROI "
        f"({best_roi.roi:+.2f}). {significance} These results come from synthetic potential "
        "outcomes and validate the trial workflow, not real deployment impact. Before serving, "
        "pre-register the primary estimand and guardrails, confirm traffic and power assumptions, "
        "then run this randomized holdout design prospectively."
    )


def render_policy_trial_report(
    data: pd.DataFrame,
    *,
    n_splits: int = 5,
    seed: int = 42,
    treatment_cost_per_user: float = 1.0,
    value_per_conversion: float = 100.0,
    traffic_allocation: float = 1.0,
    holdout_fraction: float = 0.2,
    minimum_detectable_effect_target: float = 0.02,
    alpha: float = 0.05,
    power: float = 0.80,
    n_batches: int = 5,
    guardrails: GuardrailConfig | None = None,
) -> str:
    """Render prospective policy-trial designs and synthetic results."""
    runs = run_default_policy_trials(
        data,
        n_splits=n_splits,
        seed=seed,
        treatment_cost_per_user=treatment_cost_per_user,
        value_per_conversion=value_per_conversion,
        traffic_allocation=traffic_allocation,
        holdout_fraction=holdout_fraction,
        minimum_detectable_effect_target=minimum_detectable_effect_target,
        alpha=alpha,
        power=power,
        n_batches=n_batches,
        guardrails=guardrails,
    )
    result_rows = "\n".join(
        "| {policy} | {treatment:,} | {holdout:,} | {treatment_rate:.2%} | "
        "{holdout_rate:.2%} | {lift:+.2%} | [{lower:+.2%}, {upper:+.2%}] | "
        "{p_value:.4f} | {incremental:+.2f} | ${gross:+,.2f} | ${cost:,.2f} | "
        "${net:+,.2f} | {roi:+.2f} | {status} |".format(
            policy=POLICY_LABELS[policy_rule],
            treatment=run.summary.treatment_count,
            holdout=run.summary.holdout_count,
            treatment_rate=run.summary.treatment_conversion_rate,
            holdout_rate=run.summary.holdout_conversion_rate,
            lift=run.summary.conversion_lift,
            lower=run.summary.confidence_interval_lower,
            upper=run.summary.confidence_interval_upper,
            p_value=run.summary.p_value,
            incremental=run.summary.estimated_incremental_conversions,
            gross=run.summary.gross_value,
            cost=run.summary.treatment_cost,
            net=run.summary.net_value,
            roi=run.summary.roi,
            status=run.summary.guardrail_status,
        )
        for policy_rule, run in runs.items()
    )
    power_rows = "\n".join(
        "| {policy} | {baseline:.2%} | {treatment:,} | {holdout:,} | {mde:.2%} | "
        "{target:.2%} | {required:,} | {power:.1%} |".format(
            policy=POLICY_LABELS[policy_rule],
            baseline=run.power_summary.baseline_conversion_rate,
            treatment=run.power_summary.treatment_count,
            holdout=run.power_summary.holdout_count,
            mde=run.power_summary.detectable_effect,
            target=run.power_summary.target_effect,
            required=run.power_summary.required_sample_size_per_group,
            power=run.power_summary.approximate_power_at_target,
        )
        for policy_rule, run in runs.items()
    )
    thresholds = next(iter(runs.values())).config.guardrails

    return f"""# Prospective Randomized Policy Trial Simulation

## Scope

This is a synthetic prospective simulator. Cross-fitted Logistic S-learner scores define
eligibility, eligible users are newly randomized to policy treatment or holdout, and conversions
are newly sampled from a baseline probability plus known synthetic true uplift. It is not a
deployed experiment and does not establish production impact.

- Dataset rows: {len(data):,}
- Policies: {", ".join(POLICY_LABELS.values())}
- Cross-fitting folds: {n_splits}
- Traffic allocation to trial: {traffic_allocation:.1%}
- Holdout fraction among enrolled users: {holdout_fraction:.1%}
- Randomization seed: {seed}
- Value per conversion: ${value_per_conversion:,.2f}
- Treatment cost per user: ${treatment_cost_per_user:,.2f}
- Alpha: {alpha:.3f}
- Target power: {power:.1%}
- Target minimum detectable lift: {minimum_detectable_effect_target:.2%}
- Operational monitoring batches: {n_batches}
- Guardrails: minimum sample {thresholds.minimum_sample_size:,}, maximum treatment cost {f"${thresholds.maximum_treatment_cost:,.2f}" if thresholds.maximum_treatment_cost is not None else "None"}, minimum net value ${thresholds.minimum_net_value:,.2f}, minimum ROI {thresholds.minimum_roi:+.2f}, maximum negative lift {f"{thresholds.maximum_negative_conversion_lift:.2%}" if thresholds.maximum_negative_conversion_lift is not None else "None"}

## Final randomized trial estimates

Only policy-eligible, enrolled treatment and holdout users enter these estimates.

| Policy | Treatment | Holdout | Treatment conversion | Holdout conversion | Lift | 95% CI | P-value | Incremental conversions | Gross value | Treatment cost | Net value | ROI | Guardrails |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{result_rows}

## MDE and power planning

Normal-approximation diagnostics use each policy's simulated holdout rate. Required sample size is
the approximate equal-sized count per group for the target lift.

| Policy | Baseline rate | Treatment N | Holdout N | Current-design MDE | Target lift | Required N/group | Approx. power at target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{power_rows}

## Guardrail checks

| Policy | Guardrail | Observed | Threshold | Status |
| --- | --- | ---: | --- | --- |
{_render_guardrails(runs)}

## Cumulative batch monitoring

This table is operational monitoring only. Repeatedly reading ordinary p-values does not create a
valid sequential stopping rule; formal early stopping would require a pre-specified sequential
design and adjusted error control.

| Policy | Batch | Cumulative N | Treatment | Holdout | Lift | 95% CI | P-value | Net value | ROI | Guardrails |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{_render_batches(runs)}

## Interpretation and recommended next step

{_interpret(runs)}
"""


def generate_policy_trial_report(
    data: pd.DataFrame,
    output_path: Path | str,
    **report_options: object,
) -> Path:
    """Write the prospective policy trial report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_policy_trial_report(data, **report_options),
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
    parser.add_argument("--traffic-allocation", type=float, default=1.0)
    parser.add_argument("--holdout-fraction", type=float, default=0.2)
    parser.add_argument("--mde-target", type=float, default=0.02)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--batches", type=int, default=5)
    parser.add_argument("--minimum-sample-size", type=int, default=500)
    parser.add_argument("--maximum-treatment-cost", type=float, default=10_000.0)
    parser.add_argument("--minimum-net-value", type=float, default=0.0)
    parser.add_argument("--minimum-roi", type=float, default=0.0)
    parser.add_argument("--maximum-negative-lift", type=float, default=0.0)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Read experiment data and write the prospective trial report."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    guardrails = GuardrailConfig(
        minimum_sample_size=options.minimum_sample_size,
        maximum_treatment_cost=options.maximum_treatment_cost,
        minimum_net_value=options.minimum_net_value,
        minimum_roi=options.minimum_roi,
        maximum_negative_conversion_lift=options.maximum_negative_lift,
    )
    report_path = generate_policy_trial_report(
        data,
        options.output,
        n_splits=options.folds,
        seed=options.seed,
        treatment_cost_per_user=options.treatment_cost,
        value_per_conversion=options.value_per_conversion,
        traffic_allocation=options.traffic_allocation,
        holdout_fraction=options.holdout_fraction,
        minimum_detectable_effect_target=options.mde_target,
        alpha=options.alpha,
        power=options.power,
        n_batches=options.batches,
        guardrails=guardrails,
    )
    print(f"Wrote prospective policy trial report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
