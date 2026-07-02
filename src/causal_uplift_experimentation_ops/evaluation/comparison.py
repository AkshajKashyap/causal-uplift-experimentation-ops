"""Cross-fitted model comparison with bootstrap Qini uncertainty."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.evaluation.bootstrap import (
    bootstrap_uplift_metrics,
    summarize_bootstrap_results,
)
from causal_uplift_experimentation_ops.evaluation.crossfit import (
    crossfit_uplift_model,
    oracle_score_baseline,
    random_score_baseline,
)
from causal_uplift_experimentation_ops.evaluation.metrics import (
    auuc_score,
    qini_coefficient,
    qini_curve,
    top_k_policy_summary,
)
from causal_uplift_experimentation_ops.evaluation.splitting import resolve_feature_columns
from causal_uplift_experimentation_ops.models.registry import MODEL_REGISTRY

DEFAULT_MODEL_NAMES = (
    "logistic_t_learner",
    "logistic_s_learner",
    "random_forest_t_learner",
)


@dataclass(frozen=True)
class ModelComparisonResult:
    """Metrics, bootstrap uncertainty, and OOF predictions for all comparators."""

    comparison: pd.DataFrame
    uncertainty: pd.DataFrame
    scored_predictions: dict[str, pd.DataFrame]
    feature_columns: tuple[str, ...]


def _score_metrics(scored: pd.DataFrame) -> dict[str, float]:
    qini = qini_curve(scored)
    policies = top_k_policy_summary(scored).set_index("target_fraction")
    return {
        "auuc": auuc_score(scored),
        "qini_coefficient": qini_coefficient(scored),
        "maximum_qini_gain": float(qini["qini_gain"].max()),
        "top_10_percent_uplift": float(policies.loc[0.1, "estimated_uplift"]),
        "top_20_percent_uplift": float(policies.loc[0.2, "estimated_uplift"]),
        "top_30_percent_uplift": float(policies.loc[0.3, "estimated_uplift"]),
    }


def compare_uplift_models(
    data: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
    n_bootstrap: int = 100,
) -> ModelComparisonResult:
    """Cross-fit registered models and compare them with random and oracle scores."""
    features = resolve_feature_columns(data)
    scored_predictions: dict[str, pd.DataFrame] = {}
    for model_name in DEFAULT_MODEL_NAMES:
        scored_predictions[model_name] = crossfit_uplift_model(
            data,
            MODEL_REGISTRY[model_name],
            n_splits=n_splits,
            seed=seed,
            feature_columns=features,
        )

    scored_predictions["random_baseline"] = random_score_baseline(
        data,
        n_splits=n_splits,
        seed=seed,
    )
    if "true_uplift" in data.columns:
        scored_predictions["oracle_baseline"] = oracle_score_baseline(
            data,
            n_splits=n_splits,
            seed=seed,
        )

    metric_records = [
        {"model": model_name, **_score_metrics(scored)}
        for model_name, scored in scored_predictions.items()
    ]
    comparison = pd.DataFrame.from_records(metric_records)
    if not np.isfinite(
        comparison.drop(columns="model").to_numpy(dtype=float)
    ).all():
        raise ValueError("Comparison metrics must be finite")

    random_qini = float(
        comparison.loc[comparison["model"] == "random_baseline", "qini_coefficient"].iloc[0]
    )
    comparison["qini_difference_vs_random"] = comparison["qini_coefficient"] - random_qini
    comparison["beats_random"] = comparison["qini_difference_vs_random"] > 0
    comparison["qini_rank"] = (
        comparison["qini_coefficient"].rank(method="min", ascending=False).astype(int)
    )
    comparison = comparison.sort_values("qini_rank").reset_index(drop=True)

    uncertainty_records: list[dict[str, float | str]] = []
    for model_name, scored in scored_predictions.items():
        samples = bootstrap_uplift_metrics(scored, n_bootstrap=n_bootstrap, seed=seed)
        summary = summarize_bootstrap_results(samples)
        qini_summary = summary.metric_statistics.set_index("metric").loc["qini_coefficient"]
        uncertainty_records.append(
            {
                "model": model_name,
                "qini_mean": float(qini_summary["mean"]),
                "qini_lower": float(qini_summary["2.5%"]),
                "qini_median": float(qini_summary["50%"]),
                "qini_upper": float(qini_summary["97.5%"]),
                "positive_qini_rate": summary.positive_qini_rate,
            }
        )
    uncertainty = pd.DataFrame.from_records(uncertainty_records)
    return ModelComparisonResult(
        comparison=comparison,
        uncertainty=uncertainty,
        scored_predictions=scored_predictions,
        feature_columns=features,
    )
