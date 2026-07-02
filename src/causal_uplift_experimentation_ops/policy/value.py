"""Business-value assumptions and randomized policy value estimation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PolicyValueConfig:
    """Economic assumptions and optional targeting constraints."""

    value_per_conversion: float = 100.0
    treatment_cost_per_user: float = 1.0
    budget: float | None = None
    capacity_fraction: float | None = None
    min_predicted_uplift: float | None = None

    def __post_init__(self) -> None:
        if self.value_per_conversion < 0:
            raise ValueError("value_per_conversion must be non-negative")
        if self.treatment_cost_per_user < 0:
            raise ValueError("treatment_cost_per_user must be non-negative")
        if self.budget is not None and self.budget < 0:
            raise ValueError("budget must be non-negative")
        if self.capacity_fraction is not None and not 0 <= self.capacity_fraction <= 1:
            raise ValueError("capacity_fraction must be between 0 and 1")

    def maximum_users(self, population_size: int) -> int:
        """Return the maximum selectable users under budget and capacity."""
        limits = [population_size]
        if self.capacity_fraction is not None:
            limits.append(int(np.floor(population_size * self.capacity_fraction)))
        if self.budget is not None and self.treatment_cost_per_user > 0:
            limits.append(int(np.floor(self.budget / self.treatment_cost_per_user)))
        return max(0, min(limits))


@dataclass(frozen=True)
class PolicyOutcome:
    """Offline conversion and economic value estimates for selected users."""

    policy_name: str
    selected_users: int
    selected_fraction: float
    mean_predicted_uplift: float
    treatment_conversion_rate: float
    control_conversion_rate: float
    observed_uplift: float
    estimated_incremental_conversions: float
    gross_value: float
    treatment_cost: float
    net_value: float
    roi: float
    notes: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_policy_value(
    selected: pd.DataFrame,
    population_size: int,
    config: PolicyValueConfig,
    policy_name: str,
    notes: str = "",
) -> PolicyOutcome:
    """Estimate selected-group uplift and value from randomized observed outcomes."""
    required = {"treatment", "conversion", "predicted_uplift"}
    missing = sorted(required - set(selected.columns))
    if missing:
        raise ValueError(f"Missing policy value columns: {', '.join(missing)}")

    selected_users = len(selected)
    selected_fraction = selected_users / population_size if population_size else 0.0
    mean_predicted = (
        float(selected["predicted_uplift"].mean()) if selected_users else float("nan")
    )
    treated = selected[selected["treatment"] == 1]
    control = selected[selected["treatment"] == 0]

    if len(treated) and len(control):
        treatment_rate = float(treated["conversion"].mean())
        control_rate = float(control["conversion"].mean())
        observed_uplift = treatment_rate - control_rate
        incremental_conversions = observed_uplift * selected_users
    else:
        treatment_rate = float("nan")
        control_rate = float("nan")
        observed_uplift = float("nan")
        incremental_conversions = 0.0

    gross_value = incremental_conversions * config.value_per_conversion
    treatment_cost = selected_users * config.treatment_cost_per_user
    net_value = gross_value - treatment_cost
    roi = net_value / treatment_cost if treatment_cost > 0 else float("nan")
    return PolicyOutcome(
        policy_name=policy_name,
        selected_users=selected_users,
        selected_fraction=selected_fraction,
        mean_predicted_uplift=mean_predicted,
        treatment_conversion_rate=treatment_rate,
        control_conversion_rate=control_rate,
        observed_uplift=observed_uplift,
        estimated_incremental_conversions=incremental_conversions,
        gross_value=gross_value,
        treatment_cost=treatment_cost,
        net_value=net_value,
        roi=roi,
        notes=notes,
    )
