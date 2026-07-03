"""Scenario generation and optimization for prospective policy trials."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.experiments.policy_trial import (
    PolicyTrialRun,
    approximate_power,
    minimum_detectable_effect,
    required_sample_size_per_group,
)

ALL_POSITIVE_POLICY = "Logistic S-learner / All positive uplift"
TOP_20_POLICY = "Logistic S-learner / Top 20%"
DEFAULT_HOLDOUT_FRACTIONS = (0.1, 0.2, 0.3, 0.4, 0.5)
DEFAULT_TRAFFIC_MULTIPLIERS = (1, 2, 3, 5, 10)
DEFAULT_TARGET_MDES = (0.01, 0.02, 0.03, 0.05)


@dataclass(frozen=True)
class PolicyPlanningInput:
    """Observed policy inputs used to build transparent design scenarios."""

    policy_name: str
    eligible_users_per_batch: int
    baseline_conversion_rate: float
    observed_lift: float
    value_per_conversion: float = 100.0
    treatment_cost_per_user: float = 1.0

    def __post_init__(self) -> None:
        if not self.policy_name.strip():
            raise ValueError("policy_name must not be empty")
        if self.eligible_users_per_batch <= 1:
            raise ValueError("eligible_users_per_batch must be greater than 1")
        if not 0.0 < self.baseline_conversion_rate < 1.0:
            raise ValueError("baseline_conversion_rate must be between 0 and 1")
        if self.observed_lift <= 0:
            raise ValueError("observed_lift must be positive for efficacy planning")
        if self.value_per_conversion <= 0:
            raise ValueError("value_per_conversion must be positive")
        if self.treatment_cost_per_user < 0:
            raise ValueError("treatment_cost_per_user must be non-negative")


def _group_counts(total_users: int, holdout_fraction: float) -> tuple[int, int]:
    holdout_users = min(
        max(int(round(total_users * holdout_fraction)), 1),
        total_users - 1,
    )
    return total_users - holdout_users, holdout_users


def required_total_sample_size(
    baseline_conversion_rate: float,
    target_mde: float,
    holdout_fraction: float,
    alpha: float = 0.05,
    target_power: float = 0.80,
) -> int:
    """Find the smallest total sample meeting target power for an allocation."""
    if not 0.0 < holdout_fraction < 1.0:
        raise ValueError("holdout_fraction must be between 0 and 1")
    if target_mde <= 0:
        raise ValueError("target_mde must be positive")
    if not 0.0 < target_power < 1.0:
        raise ValueError("target_power must be between 0 and 1")

    def power_for(total_users: int) -> float:
        treatment_users, holdout_users = _group_counts(total_users, holdout_fraction)
        return approximate_power(
            baseline_conversion_rate,
            target_mde,
            treatment_users,
            holdout_users,
            alpha=alpha,
        )

    lower = 2
    upper = 4
    while power_for(upper) < target_power:
        lower = upper
        upper *= 2
        if upper > 100_000_000:
            raise ValueError("Required sample size exceeds the supported planning range")
    while lower + 1 < upper:
        midpoint = (lower + upper) // 2
        if power_for(midpoint) >= target_power:
            upper = midpoint
        else:
            lower = midpoint
    return upper


def planning_inputs_from_trial_runs(
    runs: dict[str, PolicyTrialRun],
) -> tuple[PolicyPlanningInput, ...]:
    """Convert Milestone 11 trial simulations into planning inputs."""
    policy_names = {
        "positive_uplift": ALL_POSITIVE_POLICY,
        "top_20_percent": TOP_20_POLICY,
    }
    missing = sorted(set(policy_names) - set(runs))
    if missing:
        raise ValueError(f"Missing policy trial runs: {', '.join(missing)}")
    inputs = []
    for policy_rule, policy_name in policy_names.items():
        run = runs[policy_rule]
        inputs.append(
            PolicyPlanningInput(
                policy_name=policy_name,
                eligible_users_per_batch=int(
                    run.assigned_data["policy_eligible"].sum()
                ),
                baseline_conversion_rate=run.summary.holdout_conversion_rate,
                observed_lift=run.summary.conversion_lift,
                value_per_conversion=run.config.value_per_conversion,
                treatment_cost_per_user=run.config.treatment_cost_per_user,
            )
        )
    return tuple(inputs)


def generate_trial_design_scenarios(
    policy_inputs: tuple[PolicyPlanningInput, ...],
    holdout_fractions: tuple[float, ...] = DEFAULT_HOLDOUT_FRACTIONS,
    traffic_multipliers: tuple[int, ...] = DEFAULT_TRAFFIC_MULTIPLIERS,
    target_mdes: tuple[float, ...] = DEFAULT_TARGET_MDES,
    alpha: float = 0.05,
    target_power: float = 0.80,
) -> pd.DataFrame:
    """Evaluate the requested policy, allocation, traffic, and MDE grid."""
    if not policy_inputs:
        raise ValueError("policy_inputs must not be empty")
    if not holdout_fractions or not traffic_multipliers or not target_mdes:
        raise ValueError("Scenario dimensions must not be empty")
    if any(not 0.0 < value < 1.0 for value in holdout_fractions):
        raise ValueError("holdout fractions must be between 0 and 1")
    if any(value <= 0 for value in traffic_multipliers):
        raise ValueError("traffic multipliers must be positive")
    if any(value <= 0 for value in target_mdes):
        raise ValueError("target MDE values must be positive")
    if not 0.0 < alpha < 1.0 or not 0.0 < target_power < 1.0:
        raise ValueError("alpha and target_power must be between 0 and 1")

    records: list[dict[str, object]] = []
    for inputs in policy_inputs:
        for target_mde in target_mdes:
            required_equal = required_sample_size_per_group(
                inputs.baseline_conversion_rate,
                target_mde,
                alpha=alpha,
                power=target_power,
            )
            for holdout_fraction in holdout_fractions:
                total_needed = required_total_sample_size(
                    inputs.baseline_conversion_rate,
                    target_mde,
                    holdout_fraction,
                    alpha=alpha,
                    target_power=target_power,
                )
                multiplier_needed = int(
                    np.ceil(total_needed / inputs.eligible_users_per_batch)
                )
                for traffic_multiplier in traffic_multipliers:
                    total_users = (
                        inputs.eligible_users_per_batch * traffic_multiplier
                    )
                    treatment_users, holdout_users = _group_counts(
                        total_users,
                        holdout_fraction,
                    )
                    scenario_mde = minimum_detectable_effect(
                        inputs.baseline_conversion_rate,
                        treatment_users,
                        holdout_users,
                        alpha=alpha,
                        power=target_power,
                    )
                    scenario_power = approximate_power(
                        inputs.baseline_conversion_rate,
                        target_mde,
                        treatment_users,
                        holdout_users,
                        alpha=alpha,
                    )
                    observed_lift_power = approximate_power(
                        inputs.baseline_conversion_rate,
                        inputs.observed_lift,
                        treatment_users,
                        holdout_users,
                        alpha=alpha,
                    )
                    treatment_cost = (
                        treatment_users * inputs.treatment_cost_per_user
                    )
                    expected_incremental_conversions = (
                        inputs.observed_lift * treatment_users
                    )
                    expected_net_value = (
                        expected_incremental_conversions
                        * inputs.value_per_conversion
                        - treatment_cost
                    )
                    records.append(
                        {
                            "policy_name": inputs.policy_name,
                            "eligible_users_per_batch": inputs.eligible_users_per_batch,
                            "baseline_conversion_rate": inputs.baseline_conversion_rate,
                            "observed_lift": inputs.observed_lift,
                            "holdout_fraction": holdout_fraction,
                            "traffic_multiplier": traffic_multiplier,
                            "target_mde": target_mde,
                            "alpha": alpha,
                            "target_power": target_power,
                            "treatment_users": treatment_users,
                            "holdout_users": holdout_users,
                            "total_users": total_users,
                            "scenario_mde": scenario_mde,
                            "approximate_power": scenario_power,
                            "required_sample_size_per_group": required_equal,
                            "total_users_needed": total_needed,
                            "traffic_multiplier_needed": multiplier_needed,
                            "meets_target_power": scenario_power >= target_power,
                            "underpowered": scenario_power < target_power,
                            "power_at_observed_lift": observed_lift_power,
                            "meets_power_at_observed_lift": (
                                observed_lift_power >= target_power
                            ),
                            "estimated_treatment_cost": treatment_cost,
                            "rough_expected_net_value": expected_net_value,
                            "rough_expected_roi": (
                                expected_net_value / treatment_cost
                                if treatment_cost > 0
                                else float("nan")
                            ),
                        }
                    )
    return pd.DataFrame.from_records(records)


def _selected_design(
    candidates: pd.DataFrame,
    sort_columns: list[str],
    ascending: list[bool],
) -> pd.Series | None:
    if candidates.empty:
        return None
    return candidates.sort_values(sort_columns, ascending=ascending).iloc[0]


def optimize_trial_designs(
    scenarios: pd.DataFrame,
    target_mde: float = 0.02,
) -> pd.DataFrame:
    """Return one transparent optimization summary for each candidate policy."""
    required = {
        "policy_name",
        "holdout_fraction",
        "traffic_multiplier",
        "target_mde",
        "meets_target_power",
        "meets_power_at_observed_lift",
        "estimated_treatment_cost",
        "rough_expected_net_value",
    }
    missing = sorted(required - set(scenarios.columns))
    if missing:
        raise ValueError(f"Missing design scenario columns: {', '.join(missing)}")
    target_rows = scenarios[np.isclose(scenarios["target_mde"], target_mde)]
    if target_rows.empty:
        raise ValueError(f"No scenarios found for target_mde={target_mde}")

    records: list[dict[str, object]] = []
    for policy_name, policy_rows in target_rows.groupby("policy_name", sort=False):
        powered = policy_rows[policy_rows["meets_target_power"]]
        powered_observed = policy_rows[
            policy_rows["meets_power_at_observed_lift"]
        ]
        smallest_target = _selected_design(
            powered,
            ["traffic_multiplier", "estimated_treatment_cost"],
            [True, True],
        )
        smallest_observed = _selected_design(
            powered_observed,
            ["traffic_multiplier", "estimated_treatment_cost"],
            [True, True],
        )
        cheapest = _selected_design(
            powered,
            ["estimated_treatment_cost", "total_users"],
            [True, True],
        )
        highest_value = _selected_design(
            powered,
            ["rough_expected_net_value", "traffic_multiplier"],
            [False, True],
        )
        current = policy_rows[
            np.isclose(policy_rows["holdout_fraction"], 0.2)
            & (policy_rows["traffic_multiplier"] == 1)
        ].iloc[0]

        def value(row: pd.Series | None, column: str) -> object:
            return row[column] if row is not None else float("nan")

        records.append(
            {
                "policy_name": policy_name,
                "target_mde": target_mde,
                "observed_lift": current["observed_lift"],
                "current_design_power": current["approximate_power"],
                "current_design_underpowered": bool(current["underpowered"]),
                "smallest_multiplier_for_target": value(
                    smallest_target, "traffic_multiplier"
                ),
                "target_design_holdout_fraction": value(
                    smallest_target, "holdout_fraction"
                ),
                "smallest_multiplier_for_observed_lift": value(
                    smallest_observed, "traffic_multiplier"
                ),
                "observed_lift_design_holdout_fraction": value(
                    smallest_observed, "holdout_fraction"
                ),
                "recommended_traffic_multiplier": value(
                    cheapest, "traffic_multiplier"
                ),
                "recommended_holdout_fraction": value(
                    cheapest, "holdout_fraction"
                ),
                "recommended_treatment_users": value(
                    cheapest, "treatment_users"
                ),
                "recommended_holdout_users": value(cheapest, "holdout_users"),
                "recommended_power": value(cheapest, "approximate_power"),
                "recommended_treatment_cost": value(
                    cheapest, "estimated_treatment_cost"
                ),
                "recommended_expected_net_value": value(
                    cheapest, "rough_expected_net_value"
                ),
                "highest_value_traffic_multiplier": value(
                    highest_value, "traffic_multiplier"
                ),
                "highest_value_holdout_fraction": value(
                    highest_value, "holdout_fraction"
                ),
                "highest_expected_net_value": value(
                    highest_value, "rough_expected_net_value"
                ),
                "recommendation_status": (
                    "adequately_powered" if cheapest is not None else "no_powered_grid_design"
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def render_design_optimization_report(
    dataset_rows: int,
    scenarios: pd.DataFrame,
    recommendations: pd.DataFrame,
    target_mde: float = 0.02,
    target_power: float = 0.80,
) -> str:
    """Render scenario results and optimized recommendations."""
    scenario_rows = "\n".join(
        "| {policy} | {target:.1%} | {holdout:.0%} | {multiplier}x | "
        "{eligible:,} | {treatment:,} | {control:,} | {mde:.2%} | {power:.1%} | "
        "{required:,} | {total_needed:,} | {needed}x | {status} | "
        "${cost:,.0f} | ${net:+,.0f} |".format(
            policy=row.policy_name,
            target=row.target_mde,
            holdout=row.holdout_fraction,
            multiplier=row.traffic_multiplier,
            eligible=row.eligible_users_per_batch,
            treatment=row.treatment_users,
            control=row.holdout_users,
            mde=row.scenario_mde,
            power=row.approximate_power,
            required=row.required_sample_size_per_group,
            total_needed=row.total_users_needed,
            needed=row.traffic_multiplier_needed,
            status="PASS" if row.meets_target_power else "UNDERPOWERED",
            cost=row.estimated_treatment_cost,
            net=row.rough_expected_net_value,
        )
        for row in scenarios.itertuples(index=False)
    )
    recommendation_rows = "\n".join(
        "| {policy} | {multiplier:.0f}x / {holdout:.0%} | {treatment:,.0f} / "
        "{control:,.0f} | {power:.1%} | ${cost:,.0f} | ${net:+,.0f} | "
        "{smallest_target:.0f}x | {observed_multiplier:.0f}x | "
        "{highest_multiplier:.0f}x / {highest_holdout:.0%} | "
        "${highest_net:+,.0f} | {current_power:.1%} |".format(
            policy=row.policy_name,
            multiplier=row.recommended_traffic_multiplier,
            holdout=row.recommended_holdout_fraction,
            treatment=row.recommended_treatment_users,
            control=row.recommended_holdout_users,
            power=row.recommended_power,
            cost=row.recommended_treatment_cost,
            net=row.recommended_expected_net_value,
            smallest_target=row.smallest_multiplier_for_target,
            observed_multiplier=row.smallest_multiplier_for_observed_lift,
            highest_multiplier=row.highest_value_traffic_multiplier,
            highest_holdout=row.highest_value_holdout_fraction,
            highest_net=row.highest_expected_net_value,
            current_power=row.current_design_power,
        )
        for row in recommendations.itertuples(index=False)
        if row.recommendation_status == "adequately_powered"
    )
    target_rows = scenarios[
        np.isclose(scenarios["target_mde"], target_mde)
        & scenarios["meets_target_power"]
    ]
    cheapest = target_rows.sort_values("estimated_treatment_cost").iloc[0]
    highest_value = target_rows.sort_values(
        "rough_expected_net_value",
        ascending=False,
    ).iloc[0]
    current_status = recommendations.set_index("policy_name")[
        "current_design_underpowered"
    ]
    planning_inputs = scenarios.drop_duplicates("policy_name")
    input_rows = "\n".join(
        "| {policy} | {eligible:,} | {baseline:.2%} | {lift:+.2%} |".format(
            policy=row.policy_name,
            eligible=row.eligible_users_per_batch,
            baseline=row.baseline_conversion_rate,
            lift=row.observed_lift,
        )
        for row in planning_inputs.itertuples(index=False)
    )
    current_text = (
        "Both Milestone 11 designs are underpowered for a 2-point lift."
        if current_status.all()
        else "At least one Milestone 11 design reaches the target power for a 2-point lift."
    )

    return f"""# Trial Design Optimization

## Planning assumptions

- Dataset rows per accumulated batch: {dataset_rows:,}
- Policies: {", ".join(recommendations["policy_name"])}
- Target absolute MDE for recommendations: {target_mde:.2%}
- Target power: {target_power:.1%}
- Alpha: {float(scenarios["alpha"].iloc[0]):.3f}
- Holdout fractions evaluated: 10%, 20%, 30%, 40%, 50%
- Accumulated traffic multipliers evaluated: 1x, 2x, 3x, 5x, 10x
- Target MDE values evaluated: 1%, 2%, 3%, 5%

Power and MDE values are normal-approximation planning estimates. Rough expected value applies the
Milestone 11 simulated lift to future treated traffic; it is a planning assumption, not a promise.

## Policy planning inputs

| Policy | Eligible users per batch | Baseline conversion | Simulated lift assumption |
| --- | ---: | ---: | ---: |
{input_rows}

## Recommended adequately powered design by policy

The recommendation minimizes treatment cost among grid designs reaching target power for the
2-point lift. “Observed-lift multiplier” is the smallest grid multiplier powered for the larger
Milestone 11 simulated lift.

| Policy | Cheapest design (traffic / holdout) | Treatment / holdout N | Power | Cost | Rough net | Smallest target multiplier | Observed-lift multiplier | Highest-value design | Highest rough net | Current 1x/20% power |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{recommendation_rows}

## Full scenario grid

| Policy | Target MDE | Holdout | Traffic | Eligible/batch | Treatment N | Holdout N | Design MDE | Power | Required N/group | Total N needed | Needed traffic | Status | Treatment cost | Rough net value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
{scenario_rows}

## Optimization conclusions

- Cheapest adequately powered design: **{cheapest["policy_name"]}**, {cheapest["traffic_multiplier"]}x traffic with {cheapest["holdout_fraction"]:.0%} holdout (${cheapest["estimated_treatment_cost"]:,.0f} treatment cost).
- Highest rough expected value among adequately powered designs: **{highest_value["policy_name"]}**, {highest_value["traffic_multiplier"]}x traffic with {highest_value["holdout_fraction"]:.0%} holdout (${highest_value["rough_expected_net_value"]:+,.0f} expected net value).
- {current_text}

Top-20% has the higher simulated lift and ROI, but only one fifth as many eligible users arrive per
batch, so confirming a small 2-point effect requires more accumulated traffic. All-positive has
more immediate sample size and lower treatment cost for a powered validation design, but treats
lower-ranked users and therefore has lower ROI.

Before serving, use the cheapest adequately powered all-positive design as the primary validation
trial under the current 2-point-MDE objective. Treat the top-20% policy as a separately powered
eligible-population trial; do not infer its efficacy from an underpowered one-batch comparison.
"""


def generate_design_optimization_report(
    dataset_rows: int,
    scenarios: pd.DataFrame,
    recommendations: pd.DataFrame,
    output_path: Path | str,
    target_mde: float = 0.02,
    target_power: float = 0.80,
) -> Path:
    """Write the trial-design optimization report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_design_optimization_report(
            dataset_rows,
            scenarios,
            recommendations,
            target_mde=target_mde,
            target_power=target_power,
        ),
        encoding="utf-8",
    )
    return destination
