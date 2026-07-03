from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.experiments.policy_trial import (
    POLICY_HOLDOUT,
    POLICY_TREATMENT,
    GuardrailConfig,
    PolicyTrialConfig,
    analyze_policy_trial,
    assign_policy_trial,
    minimum_detectable_effect,
    required_sample_size_per_group,
    simulate_prospective_outcomes,
    simulate_trial_batches,
)
from causal_uplift_experimentation_ops.experiments.policy_trial_report import (
    generate_policy_trial_report,
)


@pytest.fixture
def scored_data() -> pd.DataFrame:
    rows = 200
    return pd.DataFrame(
        {
            "user_id": np.arange(1, rows + 1),
            "treatment": np.arange(rows) % 2,
            "conversion": (np.arange(rows) % 6 == 0).astype(int),
            "predicted_control_conversion": np.linspace(0.08, 0.18, rows),
            "predicted_treatment_conversion": np.linspace(0.12, 0.22, rows),
            "predicted_uplift": np.linspace(0.08, -0.02, rows),
            "true_uplift": np.linspace(0.06, 0.01, rows),
        }
    )


def test_trial_config_validates_correct_values() -> None:
    config = PolicyTrialConfig()

    assert config.holdout_fraction == 0.2
    assert config.traffic_allocation == 1.0


def test_invalid_holdout_fraction_raises() -> None:
    with pytest.raises(ValueError, match="holdout_fraction must be between 0 and 1"):
        PolicyTrialConfig(holdout_fraction=1.0)


def test_invalid_traffic_allocation_raises() -> None:
    with pytest.raises(ValueError, match="traffic_allocation must be between 0 and 1"):
        PolicyTrialConfig(traffic_allocation=0.0)


def test_invalid_treatment_cost_raises() -> None:
    with pytest.raises(ValueError, match="treatment_cost_per_user must be non-negative"):
        PolicyTrialConfig(treatment_cost_per_user=-1.0)


def test_assignment_is_deterministic(scored_data: pd.DataFrame) -> None:
    config = PolicyTrialConfig(randomization_seed=17)

    first = assign_policy_trial(scored_data, config)
    second = assign_policy_trial(scored_data, config)

    pd.testing.assert_frame_equal(first, second)


def test_assignment_contains_treatment_and_holdout(scored_data: pd.DataFrame) -> None:
    assigned = assign_policy_trial(scored_data, PolicyTrialConfig())

    assert {POLICY_TREATMENT, POLICY_HOLDOUT}.issubset(set(assigned["trial_group"]))


def test_noneligible_users_are_marked(scored_data: pd.DataFrame) -> None:
    config = PolicyTrialConfig(candidate_policy_rule="top_20_percent")
    assigned = assign_policy_trial(scored_data, config)

    noneligible = assigned[~assigned["policy_eligible"]]
    assert not noneligible.empty
    assert set(noneligible["trial_group"]) == {"not_eligible"}
    assert (noneligible["assigned_treatment"] == 0).all()


def test_prospective_simulation_is_deterministic(scored_data: pd.DataFrame) -> None:
    assigned = assign_policy_trial(scored_data, PolicyTrialConfig())

    first = simulate_prospective_outcomes(assigned, seed=99)
    second = simulate_prospective_outcomes(assigned, seed=99)

    pd.testing.assert_frame_equal(first, second)


def test_trial_analysis_returns_finite_metrics(scored_data: pd.DataFrame) -> None:
    config = PolicyTrialConfig(
        guardrails=GuardrailConfig(minimum_sample_size=20),
    )
    simulated = simulate_prospective_outcomes(assign_policy_trial(scored_data, config))
    summary = analyze_policy_trial(simulated, config)

    assert np.isfinite(
        [summary.conversion_lift, summary.net_value, summary.roi]
    ).all()


def test_confidence_interval_is_ordered(scored_data: pd.DataFrame) -> None:
    config = PolicyTrialConfig()
    simulated = simulate_prospective_outcomes(assign_policy_trial(scored_data, config))
    summary = analyze_policy_trial(simulated, config)

    assert summary.confidence_interval_lower <= summary.confidence_interval_upper


def test_p_value_is_valid(scored_data: pd.DataFrame) -> None:
    config = PolicyTrialConfig()
    simulated = simulate_prospective_outcomes(assign_policy_trial(scored_data, config))
    summary = analyze_policy_trial(simulated, config)

    assert 0 <= summary.p_value <= 1


def test_mde_is_positive() -> None:
    assert minimum_detectable_effect(0.1, 800, 200) > 0


def test_required_sample_size_is_positive_integer() -> None:
    required = required_sample_size_per_group(0.1, 0.02)

    assert isinstance(required, int)
    assert required > 0


def test_batch_simulation_returns_one_row_per_batch(
    scored_data: pd.DataFrame,
) -> None:
    config = PolicyTrialConfig(n_batches=5)
    simulated = simulate_prospective_outcomes(assign_policy_trial(scored_data, config))
    batches = simulate_trial_batches(simulated, config)

    assert len(batches) == 5
    assert batches["batch"].tolist() == [1, 2, 3, 4, 5]


def test_guardrail_status_contains_pass_or_fail(scored_data: pd.DataFrame) -> None:
    config = PolicyTrialConfig()
    simulated = simulate_prospective_outcomes(assign_policy_trial(scored_data, config))
    summary = analyze_policy_trial(simulated, config)

    assert set(summary.guardrails["status"]).issubset({"PASS", "FAIL"})
    assert summary.guardrail_status in {"PASS", "FAIL"}


def test_policy_trial_report_generation(tmp_path: Path) -> None:
    data = generate_synthetic_experiment(n_users=500, seed=404)
    report_path = generate_policy_trial_report(
        data,
        tmp_path / "prospective_policy_trial.md",
        n_splits=2,
        n_batches=2,
        guardrails=GuardrailConfig(minimum_sample_size=20),
    )

    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# Prospective Randomized Policy Trial Simulation" in report
    assert "operational monitoring only" in report


def test_missing_predicted_uplift_raises(scored_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Missing policy trial columns: predicted_uplift"):
        assign_policy_trial(
            scored_data.drop(columns="predicted_uplift"),
            PolicyTrialConfig(),
        )


def test_missing_true_uplift_raises(scored_data: pd.DataFrame) -> None:
    assigned = assign_policy_trial(
        scored_data.drop(columns="true_uplift"),
        PolicyTrialConfig(),
    )

    with pytest.raises(ValueError, match="Missing prospective simulation columns: true_uplift"):
        simulate_prospective_outcomes(assigned)
