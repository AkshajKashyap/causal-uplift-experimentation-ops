"""Leakage-safe splitting and uplift evaluation utilities."""

from causal_uplift_experimentation_ops.evaluation.bootstrap import (
    BootstrapSummary,
    bootstrap_uplift_metrics,
    summarize_bootstrap_results,
)
from causal_uplift_experimentation_ops.evaluation.bootstrap_report import (
    generate_bootstrap_report,
)
from causal_uplift_experimentation_ops.evaluation.comparison import (
    ModelComparisonResult,
    compare_uplift_models,
)
from causal_uplift_experimentation_ops.evaluation.comparison_report import (
    generate_comparison_report,
)
from causal_uplift_experimentation_ops.evaluation.crossfit import (
    crossfit_uplift_model,
    oracle_score_baseline,
    random_score_baseline,
    stratified_fold_assignments,
)
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
from causal_uplift_experimentation_ops.evaluation.robustness import (
    DEFAULT_ROBUSTNESS_SEEDS,
    RobustnessSummary,
    evaluate_t_learner_repeated_splits,
    summarize_repeated_split_results,
)
from causal_uplift_experimentation_ops.evaluation.robustness_report import (
    generate_robustness_report,
)
from causal_uplift_experimentation_ops.evaluation.splitting import (
    ExperimentSplit,
    split_experiment_data,
)

__all__ = [
    "BootstrapSummary",
    "DEFAULT_ROBUSTNESS_SEEDS",
    "ExperimentSplit",
    "ModelComparisonResult",
    "RobustnessSummary",
    "add_oracle_uplift_score",
    "auuc_score",
    "bootstrap_uplift_metrics",
    "compare_uplift_models",
    "crossfit_uplift_model",
    "cumulative_uplift_curve",
    "evaluate_t_learner_repeated_splits",
    "generate_robustness_report",
    "generate_bootstrap_report",
    "generate_comparison_report",
    "generate_uplift_evaluation_report",
    "qini_coefficient",
    "qini_curve",
    "oracle_score_baseline",
    "random_score_baseline",
    "split_experiment_data",
    "summarize_repeated_split_results",
    "summarize_bootstrap_results",
    "stratified_fold_assignments",
    "top_k_policy_summary",
    "uplift_ranking_table",
]
