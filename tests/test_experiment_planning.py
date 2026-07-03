from pathlib import Path

import pandas as pd
import pytest

from causal_uplift_experimentation_ops.experiments.design_optimization import (
    ALL_POSITIVE_POLICY,
    TOP_20_POLICY,
    PolicyPlanningInput,
    generate_design_optimization_report,
    generate_trial_design_scenarios,
    optimize_trial_designs,
)
from causal_uplift_experimentation_ops.experiments.preregistration import (
    PreregistrationConfig,
    generate_preregistration_report,
)


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    inputs = (
        PolicyPlanningInput(
            policy_name=ALL_POSITIVE_POLICY,
            eligible_users_per_batch=10_000,
            baseline_conversion_rate=0.112,
            observed_lift=0.0436,
        ),
        PolicyPlanningInput(
            policy_name=TOP_20_POLICY,
            eligible_users_per_batch=2_000,
            baseline_conversion_rate=0.18,
            observed_lift=0.0812,
        ),
    )
    return generate_trial_design_scenarios(inputs)


def test_preregistration_config_validates_valid_values() -> None:
    config = PreregistrationConfig()

    assert config.primary_estimand.startswith("Intent-to-treat")
    assert config.guardrail_metrics


def test_invalid_alpha_raises() -> None:
    with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
        PreregistrationConfig(alpha=1.0)


def test_invalid_target_power_raises() -> None:
    with pytest.raises(ValueError, match="target_power must be between 0 and 1"):
        PreregistrationConfig(target_power=0.0)


def test_invalid_target_mde_raises() -> None:
    with pytest.raises(ValueError, match="target_mde must be positive"):
        PreregistrationConfig(target_mde=0.0)


def test_missing_experiment_name_raises() -> None:
    with pytest.raises(ValueError, match="experiment_name must not be empty"):
        PreregistrationConfig(experiment_name=" ")


def test_preregistration_report_is_created(tmp_path: Path) -> None:
    report_path = generate_preregistration_report(
        PreregistrationConfig(),
        tmp_path / "experiment_preregistration.md",
    )

    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "## Primary estimand and hypotheses" in report
    assert "## What this experiment cannot prove" in report


def test_scenarios_include_expected_policies(scenarios: pd.DataFrame) -> None:
    assert set(scenarios["policy_name"]) == {
        ALL_POSITIVE_POLICY,
        TOP_20_POLICY,
    }


def test_scenario_grid_has_expected_number_of_rows(
    scenarios: pd.DataFrame,
) -> None:
    assert len(scenarios) == 2 * 5 * 5 * 4


def test_scenario_mde_values_are_positive(scenarios: pd.DataFrame) -> None:
    assert (scenarios["scenario_mde"] > 0).all()


def test_scenario_power_is_valid(scenarios: pd.DataFrame) -> None:
    assert scenarios["approximate_power"].between(0, 1).all()


def test_required_sample_size_is_positive(scenarios: pd.DataFrame) -> None:
    assert (scenarios["required_sample_size_per_group"] > 0).all()
    assert (scenarios["total_users_needed"] > 0).all()


def test_optimizer_recommends_each_policy(scenarios: pd.DataFrame) -> None:
    recommendations = optimize_trial_designs(scenarios)

    assert set(recommendations["policy_name"]) == {
        ALL_POSITIVE_POLICY,
        TOP_20_POLICY,
    }
    assert set(recommendations["recommendation_status"]) == {"adequately_powered"}


def test_underpowered_scenarios_are_flagged(scenarios: pd.DataFrame) -> None:
    current = scenarios[
        (scenarios["target_mde"] == 0.02)
        & (scenarios["holdout_fraction"] == 0.2)
        & (scenarios["traffic_multiplier"] == 1)
    ]

    assert current["underpowered"].all()
    assert (~current["meets_target_power"]).all()


def test_both_planning_reports_are_created(
    scenarios: pd.DataFrame,
    tmp_path: Path,
) -> None:
    preregistration_path = generate_preregistration_report(
        PreregistrationConfig(),
        tmp_path / "experiment_preregistration.md",
    )
    optimization_path = generate_design_optimization_report(
        10_000,
        scenarios,
        optimize_trial_designs(scenarios),
        tmp_path / "trial_design_optimization.md",
    )

    assert preregistration_path.exists()
    assert optimization_path.exists()
    assert "# Trial Design Optimization" in optimization_path.read_text(
        encoding="utf-8"
    )
