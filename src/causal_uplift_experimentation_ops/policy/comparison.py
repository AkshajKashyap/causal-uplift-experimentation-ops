"""Model-to-policy value comparison using cross-fitted predictions."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from causal_uplift_experimentation_ops.evaluation.comparison import (
    score_comparison_models,
)
from causal_uplift_experimentation_ops.policy.simulation import compare_policies
from causal_uplift_experimentation_ops.policy.value import PolicyValueConfig


@dataclass(frozen=True)
class ModelPolicyComparisonResult:
    """Policy outcomes for every cross-fitted model and baseline."""

    comparison: pd.DataFrame
    scored_predictions: dict[str, pd.DataFrame]
    feature_columns: tuple[str, ...]
    config: PolicyValueConfig


def compare_scored_model_policies(
    scored_predictions: dict[str, pd.DataFrame],
    config: PolicyValueConfig,
    seed: int = 42,
) -> pd.DataFrame:
    """Apply identical policy rules to already-scored model predictions."""
    policy_frames = []
    for model_name, scored in scored_predictions.items():
        policies = compare_policies(scored, config=config, seed=seed)
        policies.insert(0, "model", model_name)
        policy_frames.append(policies)
    return pd.concat(policy_frames, ignore_index=True)


def compare_model_policies(
    data: pd.DataFrame,
    config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    seed: int = 42,
) -> ModelPolicyComparisonResult:
    """Cross-fit all registered comparators and simulate identical policy rules."""
    assumptions = config or PolicyValueConfig()
    predictions, features = score_comparison_models(
        data,
        n_splits=n_splits,
        seed=seed,
    )
    comparison = compare_scored_model_policies(predictions, assumptions, seed=seed)
    return ModelPolicyComparisonResult(
        comparison=comparison,
        scored_predictions=predictions,
        feature_columns=features,
        config=assumptions,
    )
