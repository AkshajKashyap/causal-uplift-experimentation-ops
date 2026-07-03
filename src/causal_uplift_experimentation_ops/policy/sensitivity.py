"""Business-assumption sensitivity and break-even analysis for targeting policies."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import pandas as pd

from causal_uplift_experimentation_ops.evaluation.comparison import (
    DEFAULT_MODEL_NAMES,
    score_comparison_models,
)
from causal_uplift_experimentation_ops.policy.comparison import (
    compare_scored_model_policies,
)
from causal_uplift_experimentation_ops.policy.simulation import LEARNED_POLICY_NAMES
from causal_uplift_experimentation_ops.policy.value import PolicyValueConfig

DEFAULT_VALUE_PER_CONVERSION_VALUES = (25.0, 50.0, 100.0, 150.0, 200.0)
DEFAULT_TREATMENT_COST_VALUES = (0.25, 0.5, 1.0, 2.0, 5.0)
DEFAULT_CAPACITY_VALUES = (0.05, 0.1, 0.2, 0.3, 0.5)
DEFAULT_BUDGET_VALUES = (500.0, 1_000.0, 2_500.0, 5_000.0, 10_000.0)

SUPPORTED_ASSUMPTIONS = {
    "value_per_conversion",
    "treatment_cost_per_user",
    "capacity_fraction",
    "budget",
}


@dataclass(frozen=True)
class DecisionStabilitySummary:
    """How consistently model-policy recommendations win across scenarios."""

    scenario_count: int
    most_frequent_best_model: str
    most_frequent_best_policy: str
    most_frequent_model_policy: str
    same_model_win_rate: float
    same_policy_win_rate: float
    learned_beats_random_rate: float
    positive_learned_net_value_rate: float
    average_learned_oracle_ratio: float
    worst_case_learned_net_value: float
    worst_case_roi: float
    best_case_learned_net_value: float
    best_case_roi: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BreakEvenResult:
    """Break-even thresholds for the base best learned policy."""

    model: str
    policy_name: str
    maximum_treatment_cost: float
    minimum_value_per_conversion: float
    policy_thresholds: pd.DataFrame


@dataclass(frozen=True)
class PolicySensitivityResult:
    """All one-way, grid, stability, and break-even sensitivity outputs."""

    base_comparison: pd.DataFrame
    one_way: pd.DataFrame
    value_cost_grid: pd.DataFrame
    capacity_cost_grid: pd.DataFrame
    stability: DecisionStabilitySummary
    break_even: BreakEvenResult
    scored_predictions: dict[str, pd.DataFrame]
    base_config: PolicyValueConfig


def _validate_assumption_value(name: str, value: float) -> None:
    if name not in SUPPORTED_ASSUMPTIONS:
        choices = ", ".join(sorted(SUPPORTED_ASSUMPTIONS))
        raise ValueError(f"Unsupported sensitivity assumption {name!r}; choose from: {choices}")
    if name == "value_per_conversion" and value <= 0:
        raise ValueError("value_per_conversion must be greater than 0")
    if name == "treatment_cost_per_user" and value < 0:
        raise ValueError("treatment_cost_per_user must be non-negative")
    if name == "capacity_fraction" and not 0 <= value <= 1:
        raise ValueError("capacity_fraction must be between 0 and 1")
    if name == "budget" and value < 0:
        raise ValueError("budget must be non-negative")


def _scenario_config(
    base_config: PolicyValueConfig,
    changes: dict[str, float],
) -> PolicyValueConfig:
    for name, value in changes.items():
        _validate_assumption_value(name, value)
    return replace(base_config, **changes)


def _best_row(frame: pd.DataFrame, metric: str) -> pd.Series:
    finite = frame[frame[metric].notna()]
    if finite.empty:
        raise ValueError(f"No finite {metric} values are available")
    return finite.loc[finite[metric].idxmax()]


def _summarize_scenario(
    policy_table: pd.DataFrame,
    base_model: str,
    base_policy: str,
) -> dict[str, object]:
    learned = policy_table[
        policy_table["model"].isin(DEFAULT_MODEL_NAMES)
        & policy_table["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    best_net = _best_row(learned, "net_value")
    best_roi = _best_row(learned, "roi")

    random_rows = policy_table[
        policy_table["policy_name"] == "random_matched_20_percent"
    ]
    random_net_value = float(random_rows["net_value"].max())

    oracle_rows = policy_table[policy_table["model"] == "oracle_baseline"]
    oracle_net_value = (
        float(oracle_rows["net_value"].max()) if not oracle_rows.empty else float("nan")
    )
    learned_oracle_ratio = (
        float(best_net["net_value"] / oracle_net_value)
        if oracle_net_value > 0
        else float("nan")
    )
    return {
        "best_net_model": best_net["model"],
        "best_net_policy": best_net["policy_name"],
        "best_net_value": float(best_net["net_value"]),
        "best_net_selected_users": int(best_net["selected_users"]),
        "best_net_gross_value": float(best_net["gross_value"]),
        "best_roi_model": best_roi["model"],
        "best_roi_policy": best_roi["policy_name"],
        "best_roi": float(best_roi["roi"]),
        "random_net_value": random_net_value,
        "learned_random_net_difference": float(best_net["net_value"] - random_net_value),
        "learned_beats_random": bool(best_net["net_value"] > random_net_value),
        "oracle_net_value": oracle_net_value,
        "learned_oracle_net_ratio": learned_oracle_ratio,
        "recommendation_changed": bool(
            best_net["model"] != base_model or best_net["policy_name"] != base_policy
        ),
    }


def one_way_sensitivity(
    scored_predictions: dict[str, pd.DataFrame],
    assumption: str,
    values: list[float] | tuple[float, ...],
    base_config: PolicyValueConfig | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Vary one business assumption and summarize the best learned decisions."""
    assumptions = base_config or PolicyValueConfig()
    _validate_assumption_value("value_per_conversion", assumptions.value_per_conversion)
    base_table = compare_scored_model_policies(scored_predictions, assumptions, seed=seed)
    base_learned = base_table[
        base_table["model"].isin(DEFAULT_MODEL_NAMES)
        & base_table["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    base_best = _best_row(base_learned, "net_value")

    records = []
    for value in values:
        scenario_config = _scenario_config(assumptions, {assumption: float(value)})
        table = compare_scored_model_policies(scored_predictions, scenario_config, seed=seed)
        records.append(
            {
                "assumption": assumption,
                "assumption_value": float(value),
                **_summarize_scenario(
                    table,
                    base_model=str(base_best["model"]),
                    base_policy=str(base_best["policy_name"]),
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def two_way_sensitivity_grid(
    scored_predictions: dict[str, pd.DataFrame],
    first_assumption: str,
    first_values: list[float] | tuple[float, ...],
    second_assumption: str,
    second_values: list[float] | tuple[float, ...],
    base_config: PolicyValueConfig | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Evaluate every cell in a deterministic two-assumption grid."""
    if first_assumption == second_assumption:
        raise ValueError("Two-way sensitivity assumptions must be different")
    assumptions = base_config or PolicyValueConfig()
    _validate_assumption_value("value_per_conversion", assumptions.value_per_conversion)
    base_table = compare_scored_model_policies(scored_predictions, assumptions, seed=seed)
    base_learned = base_table[
        base_table["model"].isin(DEFAULT_MODEL_NAMES)
        & base_table["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    base_best = _best_row(base_learned, "net_value")

    records = []
    for first_value in first_values:
        for second_value in second_values:
            changes = {
                first_assumption: float(first_value),
                second_assumption: float(second_value),
            }
            scenario_config = _scenario_config(assumptions, changes)
            table = compare_scored_model_policies(
                scored_predictions,
                scenario_config,
                seed=seed,
            )
            records.append(
                {
                    first_assumption: float(first_value),
                    second_assumption: float(second_value),
                    **_summarize_scenario(
                        table,
                        base_model=str(base_best["model"]),
                        base_policy=str(base_best["policy_name"]),
                    ),
                }
            )
    return pd.DataFrame.from_records(records)


def summarize_decision_stability(scenarios: pd.DataFrame) -> DecisionStabilitySummary:
    """Aggregate recommendation frequencies and worst/best scenario outcomes."""
    required = {
        "best_net_model",
        "best_net_policy",
        "best_net_value",
        "best_roi",
        "learned_beats_random",
        "learned_oracle_net_ratio",
    }
    missing = sorted(required - set(scenarios.columns))
    if missing:
        raise ValueError(f"Missing sensitivity columns: {', '.join(missing)}")
    if scenarios.empty:
        raise ValueError("Sensitivity scenarios must not be empty")

    model_counts = scenarios["best_net_model"].value_counts()
    policy_counts = scenarios["best_net_policy"].value_counts()
    pairs = scenarios["best_net_model"] + " / " + scenarios["best_net_policy"]
    pair_counts = pairs.value_counts()
    return DecisionStabilitySummary(
        scenario_count=len(scenarios),
        most_frequent_best_model=str(model_counts.index[0]),
        most_frequent_best_policy=str(policy_counts.index[0]),
        most_frequent_model_policy=str(pair_counts.index[0]),
        same_model_win_rate=float(model_counts.iloc[0] / len(scenarios)),
        same_policy_win_rate=float(policy_counts.iloc[0] / len(scenarios)),
        learned_beats_random_rate=float(scenarios["learned_beats_random"].mean()),
        positive_learned_net_value_rate=float((scenarios["best_net_value"] > 0).mean()),
        average_learned_oracle_ratio=float(
            scenarios["learned_oracle_net_ratio"].dropna().mean()
        ),
        worst_case_learned_net_value=float(scenarios["best_net_value"].min()),
        worst_case_roi=float(scenarios["best_roi"].min()),
        best_case_learned_net_value=float(scenarios["best_net_value"].max()),
        best_case_roi=float(scenarios["best_roi"].max()),
    )


def break_even_analysis(
    base_comparison: pd.DataFrame,
    base_config: PolicyValueConfig | None = None,
) -> BreakEvenResult:
    """Calculate deterministic conversion-value and treatment-cost thresholds."""
    assumptions = base_config or PolicyValueConfig()
    learned = base_comparison[
        base_comparison["model"].isin(DEFAULT_MODEL_NAMES)
        & base_comparison["policy_name"].isin(LEARNED_POLICY_NAMES)
    ]
    best = _best_row(learned, "net_value")
    selected_users = int(best["selected_users"])
    incremental_conversions = float(best["estimated_incremental_conversions"])

    maximum_cost = (
        incremental_conversions * assumptions.value_per_conversion / selected_users
        if selected_users > 0
        else float("nan")
    )
    minimum_value = (
        selected_users * assumptions.treatment_cost_per_user / incremental_conversions
        if incremental_conversions > 0
        else float("nan")
    )

    policy_rows = learned[
        (learned["model"] == best["model"])
        & learned["policy_name"].isin(
            {"top_10_percent", "top_20_percent", "top_30_percent", "positive_uplift"}
        )
    ]
    thresholds = policy_rows.loc[
        :,
        ["policy_name", "selected_users", "estimated_incremental_conversions"],
    ].copy()
    thresholds["break_even_treatment_cost"] = (
        thresholds["estimated_incremental_conversions"]
        * assumptions.value_per_conversion
        / thresholds["selected_users"]
    )
    thresholds["profitable_at_base_cost"] = (
        thresholds["break_even_treatment_cost"] > assumptions.treatment_cost_per_user
    )
    return BreakEvenResult(
        model=str(best["model"]),
        policy_name=str(best["policy_name"]),
        maximum_treatment_cost=float(maximum_cost),
        minimum_value_per_conversion=float(minimum_value),
        policy_thresholds=thresholds.reset_index(drop=True),
    )


def analyze_policy_sensitivity(
    data: pd.DataFrame,
    base_config: PolicyValueConfig | None = None,
    n_splits: int = 5,
    seed: int = 42,
) -> PolicySensitivityResult:
    """Score models once and run the default one-way and two-way analyses."""
    assumptions = base_config or PolicyValueConfig()
    _validate_assumption_value("value_per_conversion", assumptions.value_per_conversion)
    predictions, _ = score_comparison_models(data, n_splits=n_splits, seed=seed)
    base_comparison = compare_scored_model_policies(predictions, assumptions, seed=seed)

    one_way_frames = [
        one_way_sensitivity(
            predictions,
            name,
            values,
            base_config=assumptions,
            seed=seed,
        )
        for name, values in (
            ("value_per_conversion", DEFAULT_VALUE_PER_CONVERSION_VALUES),
            ("treatment_cost_per_user", DEFAULT_TREATMENT_COST_VALUES),
            ("capacity_fraction", DEFAULT_CAPACITY_VALUES),
            ("budget", DEFAULT_BUDGET_VALUES),
        )
    ]
    one_way = pd.concat(one_way_frames, ignore_index=True)
    value_cost_grid = two_way_sensitivity_grid(
        predictions,
        "value_per_conversion",
        DEFAULT_VALUE_PER_CONVERSION_VALUES,
        "treatment_cost_per_user",
        DEFAULT_TREATMENT_COST_VALUES,
        assumptions,
        seed,
    )
    capacity_cost_grid = two_way_sensitivity_grid(
        predictions,
        "capacity_fraction",
        DEFAULT_CAPACITY_VALUES,
        "treatment_cost_per_user",
        DEFAULT_TREATMENT_COST_VALUES,
        assumptions,
        seed,
    )

    scenario_columns = [
        "best_net_model",
        "best_net_policy",
        "best_net_value",
        "best_roi",
        "learned_beats_random",
        "learned_oracle_net_ratio",
    ]
    all_scenarios = pd.concat(
        [
            one_way.loc[:, scenario_columns],
            value_cost_grid.loc[:, scenario_columns],
            capacity_cost_grid.loc[:, scenario_columns],
        ],
        ignore_index=True,
    )
    return PolicySensitivityResult(
        base_comparison=base_comparison,
        one_way=one_way,
        value_cost_grid=value_cost_grid,
        capacity_cost_grid=capacity_cost_grid,
        stability=summarize_decision_stability(all_scenarios),
        break_even=break_even_analysis(base_comparison, assumptions),
        scored_predictions=predictions,
        base_config=assumptions,
    )
