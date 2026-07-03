"""Design, simulate, and analyze a prospective randomized policy trial."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from causal_uplift_experimentation_ops.experiments.analysis import (
    conversion_rate_difference_confidence_interval,
    conversion_rate_difference_p_value,
)
from causal_uplift_experimentation_ops.policy.simulation import (
    target_positive_uplift,
    target_top_fraction,
)

POLICY_TREATMENT = "policy_treatment"
POLICY_HOLDOUT = "policy_holdout"
NOT_ELIGIBLE = "not_eligible"
NOT_ENROLLED = "not_enrolled"


@dataclass(frozen=True)
class GuardrailConfig:
    """Operational thresholds checked on cumulative trial results."""

    minimum_sample_size: int = 500
    maximum_treatment_cost: float | None = 10_000.0
    minimum_net_value: float = 0.0
    minimum_roi: float = 0.0
    maximum_negative_conversion_lift: float | None = 0.0

    def __post_init__(self) -> None:
        if self.minimum_sample_size <= 0:
            raise ValueError("minimum_sample_size must be positive")
        if self.maximum_treatment_cost is not None and self.maximum_treatment_cost < 0:
            raise ValueError("maximum_treatment_cost must be non-negative")
        if (
            self.maximum_negative_conversion_lift is not None
            and self.maximum_negative_conversion_lift < 0
        ):
            raise ValueError("maximum_negative_conversion_lift must be non-negative")


@dataclass(frozen=True)
class PolicyTrialConfig:
    """Design and economic assumptions for one candidate policy trial."""

    policy_name: str = "logistic_s_learner_all_positive"
    candidate_model_name: str = "logistic_s_learner"
    candidate_policy_rule: str = "positive_uplift"
    treatment_cost_per_user: float = 1.0
    value_per_conversion: float = 100.0
    traffic_allocation: float = 1.0
    holdout_fraction: float = 0.2
    randomization_seed: int = 42
    minimum_detectable_effect_target: float = 0.02
    alpha: float = 0.05
    power: float = 0.80
    n_batches: int = 5
    guardrails: GuardrailConfig = GuardrailConfig()

    def __post_init__(self) -> None:
        if not self.policy_name:
            raise ValueError("policy_name must not be empty")
        if not self.candidate_model_name:
            raise ValueError("candidate_model_name must not be empty")
        if not 0.0 < self.holdout_fraction < 1.0:
            raise ValueError("holdout_fraction must be between 0 and 1")
        if not 0.0 < self.traffic_allocation <= 1.0:
            raise ValueError("traffic_allocation must be between 0 and 1")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be between 0 and 1")
        if not 0.0 < self.power < 1.0:
            raise ValueError("power must be between 0 and 1")
        if self.treatment_cost_per_user < 0:
            raise ValueError("treatment_cost_per_user must be non-negative")
        if self.value_per_conversion <= 0:
            raise ValueError("value_per_conversion must be positive")
        if self.minimum_detectable_effect_target <= 0:
            raise ValueError("minimum_detectable_effect_target must be positive")
        if self.n_batches <= 0:
            raise ValueError("n_batches must be positive")


@dataclass(frozen=True)
class PolicyTrialSummary:
    """Causal and economic estimates from enrolled eligible users."""

    policy_name: str
    sample_size: int
    treatment_count: int
    holdout_count: int
    treatment_conversion_rate: float
    holdout_conversion_rate: float
    conversion_lift: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float
    estimated_incremental_conversions: float
    gross_value: float
    treatment_cost: float
    net_value: float
    roi: float
    guardrail_status: str
    guardrails: pd.DataFrame


@dataclass(frozen=True)
class PowerSummary:
    """Normal-approximation planning diagnostics for a two-arm trial."""

    baseline_conversion_rate: float
    treatment_count: int
    holdout_count: int
    detectable_effect: float
    target_effect: float
    required_sample_size_per_group: int
    approximate_power_at_target: float


@dataclass(frozen=True)
class PolicyTrialRun:
    """Assignment, simulated outcomes, final analysis, and batch monitoring."""

    config: PolicyTrialConfig
    assigned_data: pd.DataFrame
    simulated_data: pd.DataFrame
    summary: PolicyTrialSummary
    power_summary: PowerSummary
    batch_results: pd.DataFrame


def _validate_scored_data(scored: pd.DataFrame) -> None:
    required = {"user_id", "predicted_uplift"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"Missing policy trial columns: {', '.join(missing)}")
    if scored["user_id"].duplicated().any():
        raise ValueError("'user_id' must be unique for prospective assignment")
    if scored["predicted_uplift"].isna().any() or not np.isfinite(
        scored["predicted_uplift"]
    ).all():
        raise ValueError("'predicted_uplift' must contain only finite values")


def _eligible_user_ids(scored: pd.DataFrame, policy_rule: str) -> set[object]:
    if policy_rule == "positive_uplift":
        selected = target_positive_uplift(scored)
    elif policy_rule.startswith("top_") and policy_rule.endswith("_percent"):
        percentage_text = policy_rule.removeprefix("top_").removesuffix("_percent")
        try:
            fraction = float(percentage_text) / 100
        except ValueError as error:
            raise ValueError(f"Unsupported candidate_policy_rule: {policy_rule}") from error
        selected = target_top_fraction(scored, fraction)
    else:
        raise ValueError(f"Unsupported candidate_policy_rule: {policy_rule}")
    return set(selected["user_id"])


def assign_policy_trial(
    scored: pd.DataFrame,
    config: PolicyTrialConfig,
) -> pd.DataFrame:
    """Randomize policy-eligible traffic into treatment and holdout groups."""
    _validate_scored_data(scored)
    eligible_ids = _eligible_user_ids(scored, config.candidate_policy_rule)
    eligible_positions = np.flatnonzero(scored["user_id"].isin(eligible_ids).to_numpy())
    if len(eligible_positions) < 2:
        raise ValueError("Candidate policy must identify at least two eligible users")

    rng = np.random.default_rng(config.randomization_seed)
    shuffled = rng.permutation(eligible_positions)
    enrolled_count = int(np.floor(len(shuffled) * config.traffic_allocation))
    if enrolled_count < 2:
        raise ValueError("traffic_allocation must enroll at least two eligible users")
    enrolled = shuffled[:enrolled_count]
    holdout_count = int(round(enrolled_count * config.holdout_fraction))
    holdout_count = min(max(holdout_count, 1), enrolled_count - 1)
    holdout_positions = enrolled[:holdout_count]
    treatment_positions = enrolled[holdout_count:]

    assigned = scored.copy().reset_index(drop=True)
    assigned["policy_eligible"] = assigned["user_id"].isin(eligible_ids)
    assigned["trial_group"] = NOT_ELIGIBLE
    assigned.loc[assigned["policy_eligible"], "trial_group"] = NOT_ENROLLED
    assigned.loc[holdout_positions, "trial_group"] = POLICY_HOLDOUT
    assigned.loc[treatment_positions, "trial_group"] = POLICY_TREATMENT
    assigned["assigned_treatment"] = (
        assigned["trial_group"] == POLICY_TREATMENT
    ).astype(int)
    assigned["assignment_seed"] = config.randomization_seed
    assigned["candidate_policy_name"] = config.policy_name
    return assigned


def simulate_prospective_outcomes(
    assigned: pd.DataFrame,
    seed: int = 42,
) -> pd.DataFrame:
    """Simulate conversions from baseline probability and known synthetic uplift.

    The preferred baseline is ``baseline_conversion_probability``. Cross-fitted
    model output remains backward compatible by supplying
    ``predicted_control_conversion`` instead. Treatment probability is either
    supplied directly or computed as baseline plus synthetic ``true_uplift``.
    """
    required = {"assigned_treatment", "true_uplift"}
    missing = sorted(required - set(assigned.columns))
    if missing:
        raise ValueError(f"Missing prospective simulation columns: {', '.join(missing)}")

    if "baseline_conversion_probability" in assigned:
        baseline = assigned["baseline_conversion_probability"].to_numpy(dtype=float)
    elif "predicted_control_conversion" in assigned:
        baseline = assigned["predicted_control_conversion"].to_numpy(dtype=float)
    else:
        raise ValueError(
            "Prospective simulation requires 'baseline_conversion_probability' "
            "or 'predicted_control_conversion'"
        )
    if "treatment_conversion_probability" in assigned:
        treatment_probability = assigned["treatment_conversion_probability"].to_numpy(
            dtype=float
        )
    else:
        treatment_probability = np.clip(
            baseline + assigned["true_uplift"].to_numpy(dtype=float),
            0.0,
            1.0,
        )
    if (
        not np.isfinite(baseline).all()
        or not np.isfinite(treatment_probability).all()
        or ((baseline < 0) | (baseline > 1)).any()
        or ((treatment_probability < 0) | (treatment_probability > 1)).any()
    ):
        raise ValueError("Prospective conversion probabilities must be finite and between 0 and 1")

    assigned_treatment = assigned["assigned_treatment"].to_numpy(dtype=int)
    if not set(np.unique(assigned_treatment)).issubset({0, 1}):
        raise ValueError("'assigned_treatment' must contain only 0 and 1")
    observed_probability = np.where(
        assigned_treatment == 1,
        treatment_probability,
        baseline,
    )
    result = assigned.copy()
    result["prospective_control_probability"] = baseline
    result["prospective_treatment_probability"] = treatment_probability
    result["prospective_conversion_probability"] = observed_probability
    result["prospective_conversion"] = np.random.default_rng(seed).binomial(
        1,
        observed_probability,
    )
    return result


def approximate_proportion_difference_standard_error(
    control_rate: float,
    treatment_rate: float,
    control_count: int,
    treatment_count: int,
) -> float:
    """Return the unpooled standard error for a difference in proportions."""
    if not 0.0 <= control_rate <= 1.0 or not 0.0 <= treatment_rate <= 1.0:
        raise ValueError("Conversion rates must be between 0 and 1")
    if control_count <= 0 or treatment_count <= 0:
        raise ValueError("Group counts must be positive")
    variance = (
        control_rate * (1 - control_rate) / control_count
        + treatment_rate * (1 - treatment_rate) / treatment_count
    )
    return float(np.sqrt(variance))


def minimum_detectable_effect(
    baseline_conversion_rate: float,
    treatment_count: int,
    holdout_count: int,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """Approximate the two-sided detectable lift using a normal approximation."""
    if not 0.0 < baseline_conversion_rate < 1.0:
        raise ValueError("baseline_conversion_rate must be between 0 and 1")
    if not 0.0 < alpha < 1.0 or not 0.0 < power < 1.0:
        raise ValueError("alpha and power must be between 0 and 1")
    if treatment_count <= 0 or holdout_count <= 0:
        raise ValueError("Group counts must be positive")
    standard_error = np.sqrt(
        baseline_conversion_rate
        * (1 - baseline_conversion_rate)
        * (1 / treatment_count + 1 / holdout_count)
    )
    return float((norm.ppf(1 - alpha / 2) + norm.ppf(power)) * standard_error)


def required_sample_size_per_group(
    baseline_conversion_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Return approximate equal-sized group count for a target absolute lift."""
    if not 0.0 < baseline_conversion_rate < 1.0:
        raise ValueError("baseline_conversion_rate must be between 0 and 1")
    if detectable_effect <= 0:
        raise ValueError("detectable_effect must be positive")
    if not 0.0 < alpha < 1.0 or not 0.0 < power < 1.0:
        raise ValueError("alpha and power must be between 0 and 1")
    quantile_sum = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    sample_size = (
        2
        * baseline_conversion_rate
        * (1 - baseline_conversion_rate)
        * quantile_sum**2
        / detectable_effect**2
    )
    return max(1, int(np.ceil(sample_size)))


def approximate_power(
    baseline_conversion_rate: float,
    detectable_effect: float,
    treatment_count: int,
    holdout_count: int,
    alpha: float = 0.05,
) -> float:
    """Approximate two-sided test power at a specified conversion lift."""
    treatment_rate = float(np.clip(baseline_conversion_rate + detectable_effect, 0, 1))
    standard_error = approximate_proportion_difference_standard_error(
        baseline_conversion_rate,
        treatment_rate,
        holdout_count,
        treatment_count,
    )
    if standard_error == 0:
        return 1.0
    noncentrality = detectable_effect / standard_error
    critical = norm.ppf(1 - alpha / 2)
    power = norm.sf(critical - noncentrality) + norm.cdf(-critical - noncentrality)
    return float(np.clip(power, 0, 1))


def _guardrail_results(
    summary_values: dict[str, float | int],
    config: PolicyTrialConfig,
) -> pd.DataFrame:
    guardrails = config.guardrails
    checks: list[tuple[str, float, str, bool]] = [
        (
            "minimum_sample_size",
            float(summary_values["sample_size"]),
            f">= {guardrails.minimum_sample_size}",
            int(summary_values["sample_size"]) >= guardrails.minimum_sample_size,
        ),
        (
            "minimum_net_value",
            float(summary_values["net_value"]),
            f">= {guardrails.minimum_net_value:.2f}",
            float(summary_values["net_value"]) >= guardrails.minimum_net_value,
        ),
        (
            "minimum_roi",
            float(summary_values["roi"]),
            f">= {guardrails.minimum_roi:.2f}",
            float(summary_values["roi"]) >= guardrails.minimum_roi,
        ),
    ]
    if guardrails.maximum_treatment_cost is not None:
        checks.append(
            (
                "maximum_treatment_cost",
                float(summary_values["treatment_cost"]),
                f"<= {guardrails.maximum_treatment_cost:.2f}",
                float(summary_values["treatment_cost"])
                <= guardrails.maximum_treatment_cost,
            )
        )
    if guardrails.maximum_negative_conversion_lift is not None:
        checks.append(
            (
                "maximum_negative_conversion_lift",
                float(summary_values["conversion_lift"]),
                f">= {-guardrails.maximum_negative_conversion_lift:.4f}",
                float(summary_values["conversion_lift"])
                >= -guardrails.maximum_negative_conversion_lift,
            )
        )
    return pd.DataFrame(
        [
            {
                "guardrail": name,
                "observed": observed,
                "threshold": threshold,
                "passed": bool(passed),
                "status": "PASS" if passed else "FAIL",
            }
            for name, observed, threshold, passed in checks
        ]
    )


def analyze_policy_trial(
    simulated: pd.DataFrame,
    config: PolicyTrialConfig,
) -> PolicyTrialSummary:
    """Estimate randomized policy impact among enrolled eligible users only."""
    required = {"trial_group", "prospective_conversion"}
    missing = sorted(required - set(simulated.columns))
    if missing:
        raise ValueError(f"Missing trial analysis columns: {', '.join(missing)}")
    trial = simulated[
        simulated["trial_group"].isin({POLICY_TREATMENT, POLICY_HOLDOUT})
    ].copy()
    treatment = trial[trial["trial_group"] == POLICY_TREATMENT]
    holdout = trial[trial["trial_group"] == POLICY_HOLDOUT]
    if treatment.empty or holdout.empty:
        raise ValueError("Trial analysis requires policy treatment and holdout users")

    analysis_data = pd.DataFrame(
        {
            "treatment": (trial["trial_group"] == POLICY_TREATMENT).astype(int),
            "conversion": trial["prospective_conversion"].astype(int),
            "spend": np.zeros(len(trial)),
        }
    )
    interval = conversion_rate_difference_confidence_interval(
        analysis_data,
        confidence_level=1 - config.alpha,
    )
    p_value = conversion_rate_difference_p_value(analysis_data)
    treatment_rate = float(treatment["prospective_conversion"].mean())
    holdout_rate = float(holdout["prospective_conversion"].mean())
    conversion_lift = treatment_rate - holdout_rate
    incremental_conversions = conversion_lift * len(treatment)
    gross_value = incremental_conversions * config.value_per_conversion
    treatment_cost = len(treatment) * config.treatment_cost_per_user
    net_value = gross_value - treatment_cost
    roi = net_value / treatment_cost if treatment_cost > 0 else float("nan")

    values: dict[str, float | int] = {
        "sample_size": len(trial),
        "conversion_lift": conversion_lift,
        "treatment_cost": treatment_cost,
        "net_value": net_value,
        "roi": roi,
    }
    guardrail_table = _guardrail_results(values, config)
    overall_status = "PASS" if guardrail_table["passed"].all() else "FAIL"
    return PolicyTrialSummary(
        policy_name=config.policy_name,
        sample_size=len(trial),
        treatment_count=len(treatment),
        holdout_count=len(holdout),
        treatment_conversion_rate=treatment_rate,
        holdout_conversion_rate=holdout_rate,
        conversion_lift=conversion_lift,
        confidence_interval_lower=interval[0],
        confidence_interval_upper=interval[1],
        p_value=p_value,
        estimated_incremental_conversions=incremental_conversions,
        gross_value=gross_value,
        treatment_cost=treatment_cost,
        net_value=net_value,
        roi=roi,
        guardrail_status=overall_status,
        guardrails=guardrail_table,
    )


def summarize_trial_power(
    summary: PolicyTrialSummary,
    config: PolicyTrialConfig,
) -> PowerSummary:
    """Build planning diagnostics using the observed holdout conversion rate."""
    baseline = float(np.clip(summary.holdout_conversion_rate, 1e-6, 1 - 1e-6))
    return PowerSummary(
        baseline_conversion_rate=baseline,
        treatment_count=summary.treatment_count,
        holdout_count=summary.holdout_count,
        detectable_effect=minimum_detectable_effect(
            baseline,
            summary.treatment_count,
            summary.holdout_count,
            alpha=config.alpha,
            power=config.power,
        ),
        target_effect=config.minimum_detectable_effect_target,
        required_sample_size_per_group=required_sample_size_per_group(
            baseline,
            config.minimum_detectable_effect_target,
            alpha=config.alpha,
            power=config.power,
        ),
        approximate_power_at_target=approximate_power(
            baseline,
            config.minimum_detectable_effect_target,
            summary.treatment_count,
            summary.holdout_count,
            alpha=config.alpha,
        ),
    )


def simulate_trial_batches(
    simulated: pd.DataFrame,
    config: PolicyTrialConfig,
) -> pd.DataFrame:
    """Recompute cumulative metrics by batch for operational monitoring only."""
    trial = simulated[
        simulated["trial_group"].isin({POLICY_TREATMENT, POLICY_HOLDOUT})
    ]
    treatment_positions = np.flatnonzero(
        (trial["trial_group"] == POLICY_TREATMENT).to_numpy()
    )
    holdout_positions = np.flatnonzero((trial["trial_group"] == POLICY_HOLDOUT).to_numpy())
    if min(len(treatment_positions), len(holdout_positions)) < config.n_batches:
        raise ValueError("Each trial group must have at least one user per batch")

    rng = np.random.default_rng(config.randomization_seed + 1)
    treatment_chunks = np.array_split(rng.permutation(treatment_positions), config.n_batches)
    holdout_chunks = np.array_split(rng.permutation(holdout_positions), config.n_batches)
    cumulative_positions: list[int] = []
    records: list[dict[str, object]] = []
    for batch_index in range(config.n_batches):
        cumulative_positions.extend(treatment_chunks[batch_index].tolist())
        cumulative_positions.extend(holdout_chunks[batch_index].tolist())
        cumulative = trial.iloc[cumulative_positions]
        summary = analyze_policy_trial(cumulative, config)
        records.append(
            {
                "batch": batch_index + 1,
                "cumulative_sample_size": summary.sample_size,
                "treatment_count": summary.treatment_count,
                "holdout_count": summary.holdout_count,
                "conversion_lift": summary.conversion_lift,
                "confidence_interval_lower": summary.confidence_interval_lower,
                "confidence_interval_upper": summary.confidence_interval_upper,
                "p_value": summary.p_value,
                "cumulative_net_value": summary.net_value,
                "cumulative_roi": summary.roi,
                "guardrail_status": summary.guardrail_status,
            }
        )
    return pd.DataFrame.from_records(records)


def run_policy_trial(
    scored: pd.DataFrame,
    config: PolicyTrialConfig,
    outcome_seed: int | None = None,
) -> PolicyTrialRun:
    """Assign, simulate, analyze, and batch-monitor one candidate policy."""
    assigned = assign_policy_trial(scored, config)
    simulated = simulate_prospective_outcomes(
        assigned,
        seed=config.randomization_seed if outcome_seed is None else outcome_seed,
    )
    summary = analyze_policy_trial(simulated, config)
    return PolicyTrialRun(
        config=config,
        assigned_data=assigned,
        simulated_data=simulated,
        summary=summary,
        power_summary=summarize_trial_power(summary, config),
        batch_results=simulate_trial_batches(simulated, config),
    )
