"""Registry of custom uplift model factories."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from causal_uplift_experimentation_ops.models.base import UpliftModel
from causal_uplift_experimentation_ops.models.rf_t_learner import RandomForestTLearner
from causal_uplift_experimentation_ops.models.s_learner import LogisticSLearner
from causal_uplift_experimentation_ops.models.t_learner import LogisticTLearner

ModelFactory = Callable[[Sequence[str], int], UpliftModel]


def _logistic_t_factory(features: Sequence[str], seed: int) -> UpliftModel:
    return LogisticTLearner(features, seed=seed)


def _logistic_s_factory(features: Sequence[str], seed: int) -> UpliftModel:
    return LogisticSLearner(features, seed=seed)


def _forest_t_factory(features: Sequence[str], seed: int) -> UpliftModel:
    return RandomForestTLearner(features, seed=seed)


MODEL_REGISTRY: dict[str, ModelFactory] = {
    "logistic_t_learner": _logistic_t_factory,
    "logistic_s_learner": _logistic_s_factory,
    "random_forest_t_learner": _forest_t_factory,
}


def get_model_factory(name: str) -> ModelFactory:
    """Return a registered model factory or raise a clear error."""
    if name not in MODEL_REGISTRY:
        choices = ", ".join(sorted(MODEL_REGISTRY))
        raise ValueError(f"Unknown uplift model {name!r}; choose from: {choices}")
    return MODEL_REGISTRY[name]
