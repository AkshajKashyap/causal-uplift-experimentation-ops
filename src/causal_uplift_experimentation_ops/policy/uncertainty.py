"""Paired bootstrap uncertainty and regret for offline targeting policies."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.evaluation.comparison import (
    score_comparison_models,
)
from causal_uplift_experimentation_ops.policy.simulation import (
    LEARNED_POLICY_NAMES,
    compare_policies,
    oracle_policy,
    random_policy,
)
from causal_uplift_experimentation_ops.policy.value import (
    PolicyValueConfig,
    estimate_policy_value,
)


@dataclass(frozen=True)
class ChosenPolicy:
    """A model-policy pair included in paired uncertainty analysis."""

    model: str
    policy_name: str

    @property
    def policy_id(self) -> str:
        return f"{self.model}__{self.policy_name}"


DEFAULT_CHOSEN_POLICIES = (
    ChosenPolicy("logistic_s_learner", "positive_uplift"),
    ChosenPolicy("logistic_s_learner", "top_10_percent"),
    ChosenPolicy("logistic_s_learner", "top_20_percent"),
    ChosenPolicy("logistic_s_learner", "top_30_percent"),
    ChosenPolicy("logistic_t_learner", "top_20_percent"),
    ChosenPolicy("random_forest_t_learner", "top_20_percent"),
)


@dataclass(frozen=True)
class PolicyUncertaintyResult:
    """Raw bootstrap replicates and policy-level interval summaries."""

    bootstrap_results: pd.DataFrame
    summary: pd.DataFrame
    scored_predictions: dict[str, pd.DataFrame]
    config: PolicyValueConfig
    n_bootstrap: int


def _validate_config(config: PolicyValueConfig) -> None:
    if config.value_per_conversion <= 0:
        raise ValueError("value_per_conversion must be greater than 0")
    if config.treatment_cost_per_user < 0:
        raise ValueError("treatment_cost_per_user must be non-negative")


def _validate_aligned_predictions(scored_predictions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if not scored_predictions:
        raise ValueError("scored_predictions must not be empty")
    reference = next(iter(scored_predictions.values()))
    required = {"user_id", "treatment", "conversion", "predicted_uplift"}
    for model_name, scored in scored_predictions.items():
        missing = sorted(required - set(scored.columns))
        if missing:
            raise ValueError(f"Missing policy columns: {', '.join(missing)}")
        if len(scored) != len(reference):
            raise ValueError("Scored prediction frames must have equal row counts")
        if scored["user_id"].tolist() != reference["user_id"].tolist():
            raise ValueError(f"Scored rows are not aligned for model {model_name!r}")
        if not scored["treatment"].equals(reference["treatment"]):
            raise ValueError(f"Treatment rows are not aligned for model {model_name!r}")
    return reference


def _bootstrap_positions(
    reference: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
):
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be greater than 0")
    treatment = reference["treatment"].to_numpy()
    control_positions = np.flatnonzero(treatment == 0)
    treatment_positions = np.flatnonzero(treatment == 1)
    if not len(control_positions) or not len(treatment_positions):
        raise ValueError("'treatment' must contain both binary values 0 and 1")

    rng = np.random.default_rng(seed)
    for bootstrap_id in range(n_bootstrap):
        positions = np.concatenate(
            (
                rng.choice(control_positions, len(control_positions), replace=True),
                rng.choice(treatment_positions, len(treatment_positions), replace=True),
            )
        )
        yield bootstrap_id, rng.permutation(positions)


def _policy_record(
    bootstrap_id: int,
    model: str,
    row: pd.Series,
) -> dict[str, object]:
    return {
        "bootstrap_id": bootstrap_id,
        "policy_id": f"{model}__{row['policy_name']}",
        "model": model,
        "policy_name": row["policy_name"],
        "selected_users": int(row["selected_users"]),
        "selected_fraction": float(row["selected_fraction"]),
        "estimated_incremental_conversions": float(
            row["estimated_incremental_conversions"]
        ),
        "gross_value": float(row["gross_value"]),
        "treatment_cost": float(row["treatment_cost"]),
        "net_value": float(row["net_value"]),
        "roi": float(row["roi"]),
    }


def _add_regret_columns(records: list[dict[str, object]]) -> None:
    learned_records = [
        record
        for record in records
        if record["policy_name"] in LEARNED_POLICY_NAMES
        and record["model"] not in {"random_baseline", "oracle_baseline"}
    ]
    if not learned_records:
        return
    best_value = max(float(record["net_value"]) for record in learned_records)
    for record in learned_records:
        net_value = float(record["net_value"])
        record["best_in_bootstrap_regret"] = best_value - net_value
        record["is_bootstrap_best"] = bool(np.isclose(net_value, best_value))


def bootstrap_policy_values(
    scored_data: pd.DataFrame,
    config: PolicyValueConfig | None = None,
    n_bootstrap: int = 100,
    seed: int = 42,
    model_name: str = "model",
) -> pd.DataFrame:
    """Bootstrap every standard policy for one fixed scored data set."""
    assumptions = config or PolicyValueConfig()
    _validate_config(assumptions)
    compare_policies(scored_data, assumptions, seed=seed)

    records: list[dict[str, object]] = []
    for bootstrap_id, positions in _bootstrap_positions(scored_data, n_bootstrap, seed):
        sample = scored_data.iloc[positions].reset_index(drop=True)
        table = compare_policies(sample, assumptions, seed=seed + bootstrap_id)
        all_positive_value = float(
            table.loc[table["policy_name"] == "positive_uplift", "net_value"].iloc[0]
        )

        sample_records = [
            _policy_record(bootstrap_id, model_name, row)
            for _, row in table.iterrows()
        ]
        for record in sample_records:
            if record["policy_name"] not in LEARNED_POLICY_NAMES:
                continue
            selected_count = int(record["selected_users"])
            random_selected = random_policy(
                sample,
                selected_count,
                seed=seed + bootstrap_id,
                config=assumptions,
            )
            random_value = estimate_policy_value(
                random_selected,
                population_size=len(sample),
                config=assumptions,
                policy_name="matched_random",
            ).net_value
            oracle_value = float("nan")
            if "true_uplift" in sample:
                oracle_selected = oracle_policy(sample, selected_count, assumptions)
                oracle_value = estimate_policy_value(
                    oracle_selected,
                    population_size=len(sample),
                    config=assumptions,
                    policy_name="matched_oracle",
                ).net_value

            net_value = float(record["net_value"])
            record["matched_random_net_value"] = random_value
            record["random_regret"] = net_value - random_value
            record["beats_random"] = (
                float("nan") if selected_count == len(sample) else net_value > random_value
            )
            record["all_positive_net_value"] = all_positive_value
            record["beats_all_positive"] = (
                float("nan")
                if record["policy_name"] == "positive_uplift"
                else net_value > all_positive_value
            )
            record["oracle_net_value"] = oracle_value
            record["oracle_regret"] = (
                oracle_value - net_value if np.isfinite(oracle_value) else float("nan")
            )
        _add_regret_columns(sample_records)
        records.extend(sample_records)
    return pd.DataFrame.from_records(records)


def bootstrap_chosen_policies(
    scored_predictions: dict[str, pd.DataFrame],
    chosen_policies: tuple[ChosenPolicy, ...] = DEFAULT_CHOSEN_POLICIES,
    config: PolicyValueConfig | None = None,
    n_bootstrap: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """Bootstrap selected model-policy pairs with paired random and oracle references."""
    assumptions = config or PolicyValueConfig()
    _validate_config(assumptions)
    reference = _validate_aligned_predictions(scored_predictions)

    required_models = {policy.model for policy in chosen_policies}
    missing_models = sorted(required_models - set(scored_predictions))
    if missing_models:
        raise ValueError(f"Missing scored models: {', '.join(missing_models)}")
    for model_name in required_models:
        compare_policies(scored_predictions[model_name], assumptions, seed=seed)

    records: list[dict[str, object]] = []
    for bootstrap_id, positions in _bootstrap_positions(reference, n_bootstrap, seed):
        samples = {
            name: frame.iloc[positions].reset_index(drop=True)
            for name, frame in scored_predictions.items()
        }
        policy_tables = {
            name: compare_policies(sample, assumptions, seed=seed + bootstrap_id)
            for name, sample in samples.items()
        }
        sample_records: list[dict[str, object]] = []
        chosen_all_positive_value = float(
            policy_tables["logistic_s_learner"].loc[
                lambda frame: frame["policy_name"] == "positive_uplift",
                "net_value",
            ].iloc[0]
        )

        for specification in chosen_policies:
            table = policy_tables[specification.model]
            row = table.loc[table["policy_name"] == specification.policy_name].iloc[0]
            record = _policy_record(bootstrap_id, specification.model, row)

            selected_count = int(row["selected_users"])
            random_selected = random_policy(
                samples[specification.model],
                selected_count,
                seed=seed + bootstrap_id,
                config=assumptions,
            )
            random_outcome = estimate_policy_value(
                random_selected,
                population_size=len(reference),
                config=assumptions,
                policy_name="matched_random",
            )
            random_value = random_outcome.net_value

            oracle_value = float("nan")
            if "true_uplift" in samples[specification.model]:
                oracle_selected = oracle_policy(
                    samples[specification.model],
                    selected_count,
                    assumptions,
                )
                oracle_value = estimate_policy_value(
                    oracle_selected,
                    population_size=len(reference),
                    config=assumptions,
                    policy_name="matched_oracle",
                ).net_value

            net_value = float(record["net_value"])
            record.update(
                {
                    "matched_random_net_value": random_value,
                    "random_regret": net_value - random_value,
                    "beats_random": (
                        float("nan")
                        if selected_count == len(reference)
                        else net_value > random_value
                    ),
                    "all_positive_net_value": chosen_all_positive_value,
                    "beats_all_positive": (
                        float("nan")
                        if specification.policy_id
                        == "logistic_s_learner__positive_uplift"
                        else net_value > chosen_all_positive_value
                    ),
                    "oracle_net_value": oracle_value,
                    "oracle_regret": (
                        oracle_value - net_value
                        if np.isfinite(oracle_value)
                        else float("nan")
                    ),
                }
            )
            sample_records.append(record)

        if "random_baseline" in policy_tables:
            random_row = policy_tables["random_baseline"].loc[
                lambda frame: frame["policy_name"] == "random_matched_20_percent"
            ].iloc[0]
            sample_records.append(_policy_record(bootstrap_id, "random_baseline", random_row))
        if "oracle_baseline" in policy_tables:
            oracle_row = policy_tables["oracle_baseline"].loc[
                lambda frame: frame["policy_name"] == "oracle_matched_20_percent"
            ].iloc[0]
            sample_records.append(_policy_record(bootstrap_id, "oracle_baseline", oracle_row))

        _add_regret_columns(sample_records)
        records.extend(sample_records)
    return pd.DataFrame.from_records(records)


def _finite_statistic(series: pd.Series, statistic: str) -> float:
    finite = series.dropna()
    if finite.empty:
        return float("nan")
    if statistic == "mean":
        return float(finite.mean())
    if statistic == "std":
        return float(finite.std(ddof=0))
    if statistic == "median":
        return float(finite.median())
    quantiles = {"2.5%": 0.025, "50%": 0.5, "97.5%": 0.975}
    return float(finite.quantile(quantiles[statistic]))


def summarize_policy_bootstrap(results: pd.DataFrame) -> pd.DataFrame:
    """Summarize value, ROI, paired comparisons, and regret by policy."""
    required = {
        "bootstrap_id",
        "policy_id",
        "model",
        "policy_name",
        "net_value",
        "roi",
    }
    missing = sorted(required - set(results.columns))
    if missing:
        raise ValueError(f"Missing policy bootstrap columns: {', '.join(missing)}")

    records = []
    for policy_id, group in results.groupby("policy_id", sort=False):
        first = group.iloc[0]
        record: dict[str, object] = {
            "policy_id": policy_id,
            "model": first["model"],
            "policy_name": first["policy_name"],
            "mean_net_value": _finite_statistic(group["net_value"], "mean"),
            "std_net_value": _finite_statistic(group["net_value"], "std"),
            "net_value_2_5": _finite_statistic(group["net_value"], "2.5%"),
            "net_value_50": _finite_statistic(group["net_value"], "50%"),
            "net_value_97_5": _finite_statistic(group["net_value"], "97.5%"),
            "probability_positive_net_value": float((group["net_value"] > 0).mean()),
            "mean_roi": _finite_statistic(group["roi"], "mean"),
            "roi_2_5": _finite_statistic(group["roi"], "2.5%"),
            "roi_50": _finite_statistic(group["roi"], "50%"),
            "roi_97_5": _finite_statistic(group["roi"], "97.5%"),
            "probability_positive_roi": float((group["roi"] > 0).mean()),
        }
        for source, target in (
            ("beats_random", "probability_beats_random"),
            ("beats_all_positive", "probability_beats_all_positive"),
            ("is_bootstrap_best", "probability_bootstrap_best"),
        ):
            record[target] = (
                float(group[source].dropna().mean())
                if source in group and not group[source].dropna().empty
                else float("nan")
            )

        if "oracle_regret" in group:
            record.update(
                {
                    "mean_oracle_regret": _finite_statistic(
                        group["oracle_regret"], "mean"
                    ),
                    "median_oracle_regret": _finite_statistic(
                        group["oracle_regret"], "median"
                    ),
                    "oracle_regret_2_5": _finite_statistic(
                        group["oracle_regret"], "2.5%"
                    ),
                    "oracle_regret_97_5": _finite_statistic(
                        group["oracle_regret"], "97.5%"
                    ),
                }
            )
        if "best_in_bootstrap_regret" in group:
            record["mean_bootstrap_best_regret"] = _finite_statistic(
                group["best_in_bootstrap_regret"], "mean"
            )
        records.append(record)
    return pd.DataFrame.from_records(records)


def analyze_policy_uncertainty(
    data: pd.DataFrame,
    config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    n_bootstrap: int = 100,
    seed: int = 42,
) -> PolicyUncertaintyResult:
    """Cross-fit models once and bootstrap the selected policy candidates."""
    assumptions = config or PolicyValueConfig()
    _validate_config(assumptions)
    predictions, _ = score_comparison_models(data, n_splits=n_splits, seed=seed)
    bootstrap_results = bootstrap_chosen_policies(
        predictions,
        config=assumptions,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    return PolicyUncertaintyResult(
        bootstrap_results=bootstrap_results,
        summary=summarize_policy_bootstrap(bootstrap_results),
        scored_predictions=predictions,
        config=assumptions,
        n_bootstrap=n_bootstrap,
    )
