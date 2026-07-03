"""Structured pre-registration for a prospective randomized policy experiment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from causal_uplift_experimentation_ops.experiments.policy_trial import (
    required_sample_size_per_group,
)


@dataclass(frozen=True)
class PreregistrationConfig:
    """Pre-specified estimands, hypotheses, rules, and planning assumptions."""

    experiment_name: str = "Prospective uplift-policy randomized holdout trial"
    policy_under_test: str = "Logistic S-learner / All positive uplift"
    model_under_test: str = "Logistic S-learner"
    motivation: str = (
        "Validate that acting on the cross-fitted uplift policy causes incremental conversion "
        "and economic value rather than merely looking favorable in offline analysis."
    )
    primary_estimand: str = (
        "Intent-to-treat conversion lift among policy-eligible users."
    )
    primary_outcome: str = "Binary conversion during the pre-specified outcome window."
    secondary_outcomes: tuple[str, ...] = (
        "net value",
        "ROI",
        "incremental conversions",
        "treatment cost",
    )
    treatment_definition: str = (
        "Assignment to receive the intervention selected by the frozen candidate policy."
    )
    control_definition: str = (
        "Assignment to the randomized policy holdout; no intervention is delivered."
    )
    eligible_population_definition: str = (
        "Users satisfying the frozen candidate policy rule before randomization."
    )
    exclusion_rules: tuple[str, ...] = (
        "Exclude users missing a stable identifier or required pre-treatment features.",
        "Exclude users already exposed to the intervention during the trial window.",
        "Apply exclusions before randomization and do not condition on post-treatment behavior.",
    )
    randomization_unit: str = "User"
    analysis_population: str = (
        "All randomized eligible users analyzed by assigned group (intent to treat)."
    )
    null_hypothesis: str = (
        "The eligible-population conversion rate is equal under policy treatment and holdout."
    )
    alternative_hypothesis: str = (
        "The eligible-population conversion rate differs between policy treatment and holdout."
    )
    alpha: float = 0.05
    target_power: float = 0.80
    target_mde: float = 0.02
    expected_baseline_conversion_rate: float = 0.12
    value_per_conversion: float = 100.0
    treatment_cost_per_user: float = 1.0
    guardrail_metrics: tuple[str, ...] = (
        "Minimum enrolled sample size is reached.",
        "Treatment cost does not exceed its approved maximum.",
        "Estimated net value is positive.",
        "Estimated ROI meets the configured minimum.",
        "Conversion lift does not cross the maximum tolerated negative threshold.",
    )
    decision_rules: tuple[str, ...] = (
        "Deploy only if conversion lift is positive and the two-sided p-value is below alpha.",
        "Require positive estimated net value and ROI at or above the configured minimum.",
        "Require every pre-specified guardrail to pass.",
        "If any deployment condition fails, do not deploy and investigate before a new test.",
    )
    stopping_rules: tuple[str, ...] = (
        "Analyze the primary hypothesis after the pre-specified sample size or duration is met.",
        "Batch summaries are operational diagnostics, not unadjusted statistical stopping rules.",
        "Any safety stop must be documented independently of the efficacy decision.",
    )
    analysis_plan: tuple[str, ...] = (
        "Estimate treatment-minus-holdout conversion rates among eligible randomized users.",
        "Report a two-sided confidence interval and p-value for the conversion-rate difference.",
        "Scale intent-to-treat lift by treated users for incremental conversions and value.",
        "Report treatment cost, net value, ROI, exclusions, and all guardrail outcomes.",
    )
    limitations: tuple[str, ...] = (
        "Normal-approximation power calculations are planning approximations.",
        "The trial identifies impact for the tested population, policy version, and intervention.",
        "A successful trial does not guarantee stability under future drift or changed economics.",
        "Synthetic simulations validate workflow behavior but are not production evidence.",
    )

    def __post_init__(self) -> None:
        for field_name, value in (
            ("experiment_name", self.experiment_name),
            ("policy_under_test", self.policy_under_test),
            ("model_under_test", self.model_under_test),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be between 0 and 1")
        if not 0.0 < self.target_power < 1.0:
            raise ValueError("target_power must be between 0 and 1")
        if self.target_mde <= 0:
            raise ValueError("target_mde must be positive")
        if not 0.0 < self.expected_baseline_conversion_rate < 1.0:
            raise ValueError("expected_baseline_conversion_rate must be between 0 and 1")
        if self.value_per_conversion <= 0:
            raise ValueError("value_per_conversion must be positive")
        if self.treatment_cost_per_user < 0:
            raise ValueError("treatment_cost_per_user must be non-negative")
        if not self.guardrail_metrics:
            raise ValueError("At least one guardrail metric is required")


def _bullet_list(values: tuple[str, ...]) -> str:
    return "\n".join(f"- {value}" for value in values)


def render_preregistration(config: PreregistrationConfig) -> str:
    """Render a professional, explicit pre-registration Markdown artifact."""
    required_per_group = required_sample_size_per_group(
        config.expected_baseline_conversion_rate,
        config.target_mde,
        alpha=config.alpha,
        power=config.target_power,
    )
    return f"""# {config.experiment_name}

## Registration summary

- Model under test: **{config.model_under_test}**
- Policy under test: **{config.policy_under_test}**
- Registration status: **Planning artifact; freeze before enrollment**

## Motivation

{config.motivation}

## Primary estimand and hypotheses

- Primary estimand: **{config.primary_estimand}**
- Null hypothesis: {config.null_hypothesis}
- Alternative hypothesis: {config.alternative_hypothesis}
- Two-sided alpha: {config.alpha:.3f}

## Treatment, control, and eligible population

- Treatment: {config.treatment_definition}
- Control/holdout: {config.control_definition}
- Eligible population: {config.eligible_population_definition}
- Randomization unit: {config.randomization_unit}
- Analysis population: {config.analysis_population}

### Exclusion rules

{_bullet_list(config.exclusion_rules)}

## Outcomes

- Primary outcome: **{config.primary_outcome}**
- Secondary outcomes:
{_bullet_list(config.secondary_outcomes)}

## Randomization plan

Randomize policy-eligible users to policy treatment or holdout using a reproducible assignment
mechanism. Preserve assignment regardless of receipt or compliance and analyze by original
assignment. The final holdout fraction and traffic duration must be frozen before enrollment.

## Sample-size and power plan

- Expected holdout conversion rate: {config.expected_baseline_conversion_rate:.2%}
- Target absolute MDE: {config.target_mde:.2%}
- Target power: {config.target_power:.1%}
- Approximate equal-allocation requirement: **{required_per_group:,} users per group**
- Approximate total under equal allocation: **{2 * required_per_group:,} users**

These are normal-approximation planning estimates. The final design must account for its actual
treatment/holdout allocation and should be selected from the design-optimization artifact.

## Guardrails

{_bullet_list(config.guardrail_metrics)}

## Decision rules

{_bullet_list(config.decision_rules)}

## Stopping rules

{_bullet_list(config.stopping_rules)}

## Analysis plan

{_bullet_list(config.analysis_plan)}

## What this experiment can prove

Under successful randomization, adequate power, complete follow-up, and the frozen analysis plan,
the experiment can estimate whether assignment to this policy intervention caused incremental
conversion and economic value for the tested eligible population during the trial.

## What this experiment cannot prove

It cannot prove individual-level treatment effects, impact outside the eligible population,
permanent performance under drift, or value under different costs and conversion economics. It
also cannot turn synthetic simulator results into evidence of real-world impact.

## Limitations

{_bullet_list(config.limitations)}
"""


def generate_preregistration_report(
    config: PreregistrationConfig,
    output_path: Path | str,
) -> Path:
    """Write a pre-registration artifact to disk."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_preregistration(config), encoding="utf-8")
    return destination
