"""Generate experiment pre-registration and trial-design optimization reports."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.data.validation import validate_experiment_data
from causal_uplift_experimentation_ops.experiments.design_optimization import (
    ALL_POSITIVE_POLICY,
    DEFAULT_TARGET_MDES,
    generate_design_optimization_report,
    generate_trial_design_scenarios,
    optimize_trial_designs,
    planning_inputs_from_trial_runs,
)
from causal_uplift_experimentation_ops.experiments.policy_trial import (
    GuardrailConfig,
    PolicyTrialRun,
)
from causal_uplift_experimentation_ops.experiments.policy_trial_report import (
    run_default_policy_trials,
)
from causal_uplift_experimentation_ops.experiments.preregistration import (
    PreregistrationConfig,
    generate_preregistration_report,
)

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_PREREGISTRATION_PATH = Path("reports/experiment_preregistration.md")
DEFAULT_OPTIMIZATION_PATH = Path("reports/trial_design_optimization.md")


@dataclass(frozen=True)
class PlanningReportResult:
    """Paths and in-memory results from the experiment-planning workflow."""

    preregistration_path: Path
    optimization_path: Path
    scenarios: pd.DataFrame
    recommendations: pd.DataFrame
    trial_runs: dict[str, PolicyTrialRun]
    preregistration: PreregistrationConfig


def generate_experiment_planning_reports(
    data: pd.DataFrame,
    preregistration_path: Path | str = DEFAULT_PREREGISTRATION_PATH,
    optimization_path: Path | str = DEFAULT_OPTIMIZATION_PATH,
    *,
    n_splits: int = 5,
    seed: int = 42,
    target_mde: float = 0.02,
    target_power: float = 0.80,
    alpha: float = 0.05,
    value_per_conversion: float = 100.0,
    treatment_cost_per_user: float = 1.0,
) -> PlanningReportResult:
    """Recompute policy trials and write both disciplined planning artifacts."""
    guardrails = GuardrailConfig()
    runs = run_default_policy_trials(
        data,
        n_splits=n_splits,
        seed=seed,
        treatment_cost_per_user=treatment_cost_per_user,
        value_per_conversion=value_per_conversion,
        minimum_detectable_effect_target=target_mde,
        alpha=alpha,
        power=target_power,
        guardrails=guardrails,
    )
    policy_inputs = planning_inputs_from_trial_runs(runs)
    target_mdes = tuple(sorted({*DEFAULT_TARGET_MDES, target_mde}))
    scenarios = generate_trial_design_scenarios(
        policy_inputs,
        target_mdes=target_mdes,
        alpha=alpha,
        target_power=target_power,
    )
    recommendations = optimize_trial_designs(scenarios, target_mde=target_mde)
    all_positive = runs["positive_uplift"]
    preregistration = PreregistrationConfig(
        policy_under_test=ALL_POSITIVE_POLICY,
        model_under_test="Logistic S-learner",
        alpha=alpha,
        target_power=target_power,
        target_mde=target_mde,
        expected_baseline_conversion_rate=(
            all_positive.summary.holdout_conversion_rate
        ),
        value_per_conversion=value_per_conversion,
        treatment_cost_per_user=treatment_cost_per_user,
        guardrail_metrics=tuple(
            f"{row.guardrail}: {row.threshold}"
            for row in all_positive.summary.guardrails.itertuples(index=False)
        ),
    )
    preregistration_output = generate_preregistration_report(
        preregistration,
        preregistration_path,
    )
    optimization_output = generate_design_optimization_report(
        len(data),
        scenarios,
        recommendations,
        optimization_path,
        target_mde=target_mde,
        target_power=target_power,
    )
    return PlanningReportResult(
        preregistration_path=preregistration_output,
        optimization_path=optimization_output,
        scenarios=scenarios,
        recommendations=recommendations,
        trial_runs=runs,
        preregistration=preregistration,
    )


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument(
        "--preregistration-output",
        type=Path,
        default=DEFAULT_PREREGISTRATION_PATH,
    )
    parser.add_argument(
        "--optimization-output",
        type=Path,
        default=DEFAULT_OPTIMIZATION_PATH,
    )
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-mde", type=float, default=0.02)
    parser.add_argument("--target-power", type=float, default=0.80)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--value-per-conversion", type=float, default=100.0)
    parser.add_argument("--treatment-cost", type=float, default=1.0)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate both experiment-planning Markdown artifacts."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    result = generate_experiment_planning_reports(
        data,
        preregistration_path=options.preregistration_output,
        optimization_path=options.optimization_output,
        n_splits=options.folds,
        seed=options.seed,
        target_mde=options.target_mde,
        target_power=options.target_power,
        alpha=options.alpha,
        value_per_conversion=options.value_per_conversion,
        treatment_cost_per_user=options.treatment_cost,
    )
    print(f"Wrote experiment pre-registration to {result.preregistration_path}")
    print(f"Wrote trial design optimization to {result.optimization_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
