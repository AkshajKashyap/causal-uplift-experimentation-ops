from pathlib import Path

import pandas as pd
import pytest

from causal_uplift_experimentation_ops.data import generate_synthetic_experiment
from causal_uplift_experimentation_ops.experiments import (
    conversion_rate_by_group,
    conversion_rate_difference_confidence_interval,
    conversion_treatment_effect,
    generate_ab_report,
    summarize_experiment,
    treatment_control_summary,
)


@pytest.fixture
def tiny_experiment() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "treatment": [0, 0, 1, 1],
            "conversion": [0, 1, 1, 1],
            "spend": [0.0, 10.0, 12.0, 20.0],
        }
    )


def test_treatment_control_counts(tiny_experiment: pd.DataFrame) -> None:
    summary = treatment_control_summary(tiny_experiment)

    assert summary.loc["control", "count"] == 2
    assert summary.loc["treatment", "count"] == 2


def test_conversion_rate_calculation(tiny_experiment: pd.DataFrame) -> None:
    rates = conversion_rate_by_group(tiny_experiment)

    assert rates["control"] == pytest.approx(0.5)
    assert rates["treatment"] == pytest.approx(1.0)


def test_treatment_effect_on_hand_made_data(tiny_experiment: pd.DataFrame) -> None:
    assert conversion_treatment_effect(tiny_experiment) == pytest.approx(0.5)


def test_confidence_interval_has_valid_bounds() -> None:
    data = generate_synthetic_experiment(n_users=500, seed=8)

    lower, upper = conversion_rate_difference_confidence_interval(data)

    assert -1.0 <= lower <= upper <= 1.0
    assert lower <= conversion_treatment_effect(data) <= upper


def test_report_generation_creates_markdown_file(tmp_path: Path) -> None:
    data = generate_synthetic_experiment(n_users=500, seed=10)
    report_path = generate_ab_report(data, tmp_path / "ab_summary.md")

    assert report_path.exists()
    assert report_path.suffix == ".md"
    assert "# Synthetic A/B Experiment Summary" in report_path.read_text(encoding="utf-8")


def test_non_binary_treatment_raises_clear_error(tiny_experiment: pd.DataFrame) -> None:
    invalid = tiny_experiment.copy()
    invalid.loc[0, "treatment"] = 2

    with pytest.raises(ValueError, match="'treatment' must contain only 0 and 1"):
        summarize_experiment(invalid)
