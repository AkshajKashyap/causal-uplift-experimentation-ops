"""Baseline analysis for randomized A/B experiments."""

from causal_uplift_experimentation_ops.experiments.analysis import (
    ExperimentSummary,
    average_spend_by_group,
    conversion_rate_by_group,
    conversion_rate_difference_confidence_interval,
    conversion_rate_difference_p_value,
    conversion_relative_lift,
    conversion_treatment_effect,
    numeric_covariate_balance,
    spend_treatment_effect,
    summarize_experiment,
    treatment_control_summary,
)
from causal_uplift_experimentation_ops.experiments.report import generate_ab_report

__all__ = [
    "ExperimentSummary",
    "average_spend_by_group",
    "conversion_rate_by_group",
    "conversion_rate_difference_confidence_interval",
    "conversion_rate_difference_p_value",
    "conversion_relative_lift",
    "conversion_treatment_effect",
    "generate_ab_report",
    "numeric_covariate_balance",
    "spend_treatment_effect",
    "summarize_experiment",
    "treatment_control_summary",
]
