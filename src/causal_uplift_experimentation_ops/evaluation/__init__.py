"""Leakage-safe splitting and uplift evaluation utilities."""

from causal_uplift_experimentation_ops.evaluation.metrics import (
    auuc_score,
    cumulative_uplift_curve,
    qini_coefficient,
    qini_curve,
    top_k_policy_summary,
    uplift_ranking_table,
)
from causal_uplift_experimentation_ops.evaluation.oracle import add_oracle_uplift_score
from causal_uplift_experimentation_ops.evaluation.report import (
    generate_uplift_evaluation_report,
)
from causal_uplift_experimentation_ops.evaluation.splitting import (
    ExperimentSplit,
    split_experiment_data,
)

__all__ = [
    "ExperimentSplit",
    "add_oracle_uplift_score",
    "auuc_score",
    "cumulative_uplift_curve",
    "generate_uplift_evaluation_report",
    "qini_coefficient",
    "qini_curve",
    "split_experiment_data",
    "top_k_policy_summary",
    "uplift_ranking_table",
]
