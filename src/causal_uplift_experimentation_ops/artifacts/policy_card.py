"""Versioned policy decision configuration and policy-card reporting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_uplift_experimentation_ops.artifacts.manifest import DatasetFingerprint
from causal_uplift_experimentation_ops.models.t_learner import LEAKAGE_COLUMNS

DEFAULT_FEATURE_COLUMNS = (
    "age",
    "prior_purchases",
    "avg_order_value",
    "days_since_last_purchase",
    "channel",
)


@dataclass(frozen=True)
class PolicyDecisionConfig:
    """Frozen model, policy, economics, evidence, and intended-use contract."""

    artifact_version: str = "1.0.0"
    model_name: str = "logistic_s_learner"
    policy_name: str = "all_positive_uplift"
    policy_rule: str = "predicted_uplift > 0"
    selected_feature_columns: tuple[str, ...] = DEFAULT_FEATURE_COLUMNS
    value_per_conversion: float = 100.0
    treatment_cost_per_user: float = 1.0
    capacity_fraction: float | None = None
    budget: float | None = None
    experiment_preregistration_path: str = "reports/experiment_preregistration.md"
    evaluation_report_paths: tuple[str, ...] = (
        "reports/crossfit_model_comparison.md",
        "reports/targeting_policy_simulation.md",
        "reports/policy_sensitivity_analysis.md",
        "reports/policy_value_uncertainty.md",
        "reports/prospective_policy_trial.md",
        "reports/trial_design_optimization.md",
    )
    recommended_trial_design: str = (
        "Before production serving, run the all-positive randomized validation at 1x accumulated "
        "traffic with a 50% holdout."
    )
    training_data_fingerprint: str = "uncomputed"
    creation_timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    random_seed: int = 42
    limitations: tuple[str, ...] = (
        "The policy has been trained and evaluated only on synthetic data.",
        "Prospective real-world randomized validation is required before deployment.",
        "All-positive wins without budget or capacity constraints largely because broad treatment "
        "is profitable under the configured economics.",
        "Ranking quality matters more when treatment capacity or budget is constrained.",
        "Economic conclusions may change with treatment cost or conversion value.",
    )
    intended_use: str = (
        "Auditable offline batch scoring and prospective randomized policy validation."
    )
    out_of_scope_use: str = (
        "Automated production treatment, high-stakes individual decisions, or use outside the "
        "documented population without new validation."
    )

    def __post_init__(self) -> None:
        for field_name, value in (
            ("artifact_version", self.artifact_version),
            ("model_name", self.model_name),
            ("policy_name", self.policy_name),
            ("policy_rule", self.policy_rule),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if not self.selected_feature_columns:
            raise ValueError("selected_feature_columns must not be empty")
        if self.value_per_conversion <= 0:
            raise ValueError("value_per_conversion must be positive")
        if self.treatment_cost_per_user < 0:
            raise ValueError("treatment_cost_per_user must be non-negative")
        if self.capacity_fraction is not None and not 0 < self.capacity_fraction <= 1:
            raise ValueError("capacity_fraction must be between 0 and 1")
        if self.budget is not None and self.budget < 0:
            raise ValueError("budget must be non-negative")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        result = asdict(self)
        result["selected_feature_columns"] = list(self.selected_feature_columns)
        result["evaluation_report_paths"] = list(self.evaluation_report_paths)
        result["limitations"] = list(self.limitations)
        return result

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> PolicyDecisionConfig:
        """Restore tuple fields from persisted JSON."""
        restored = dict(values)
        for field_name in (
            "selected_feature_columns",
            "evaluation_report_paths",
            "limitations",
        ):
            if field_name in restored:
                restored[field_name] = tuple(restored[field_name])
        return cls(**restored)


def load_policy_config(artifact_directory: Path | str) -> PolicyDecisionConfig:
    """Load the frozen policy configuration."""
    path = Path(artifact_directory) / "policy_config.json"
    if not path.exists():
        raise ValueError(f"Policy configuration not found: {path}")
    return PolicyDecisionConfig.from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def _bullet_list(values: tuple[str, ...]) -> str:
    return "\n".join(f"- {value}" for value in values)


def render_policy_card(
    config: PolicyDecisionConfig,
    dataset_fingerprint: DatasetFingerprint,
    config_fingerprint: str,
) -> str:
    """Render the frozen policy's intended use, evidence, and risks."""
    feature_list = ", ".join(f"`{feature}`" for feature in config.selected_feature_columns)
    excluded = ", ".join(f"`{column}`" for column in sorted(LEAKAGE_COLUMNS))
    evidence = "\n".join(f"- `{path}`" for path in config.evaluation_report_paths)
    return f"""# Policy Card: {config.policy_name}

## Frozen decision

- Artifact version: **{config.artifact_version}**
- Model: **{config.model_name}**
- Policy: **{config.policy_name}**
- Decision rule: **{config.policy_rule}**
- Created: {config.creation_timestamp}
- Random seed: {config.random_seed}
- Config fingerprint: `{config_fingerprint}`

## Intended use

{config.intended_use}

## Out-of-scope use

{config.out_of_scope_use}

## Inputs and leakage controls

- Required features: {feature_list}
- Explicitly excluded identifiers, outcomes, treatment, and synthetic/debug fields: {excluded}
- Missing numeric and categorical feature values use the fitted training-time preprocessing.
- Unknown categorical levels are ignored by the fitted one-hot encoder.

## Training data summary

- Rows: {dataset_fingerprint.rows:,}
- Columns: {dataset_fingerprint.columns_count}
- Dataset fingerprint: `{dataset_fingerprint.fingerprint}`
- Content SHA-256: `{dataset_fingerprint.content_sha256}`
- Validation scope: synthetic randomized experiment data only

## Value and capacity assumptions

- Value per conversion: ${config.value_per_conversion:,.2f}
- Treatment cost per user: ${config.treatment_cost_per_user:,.2f}
- Capacity constraint: {f"{config.capacity_fraction:.1%}" if config.capacity_fraction is not None else "None"}
- Budget constraint: {f"${config.budget:,.2f}" if config.budget is not None else "None"}

## Evaluation summary

Cross-fitted model comparison, randomized-data policy value estimation, and synthetic prospective
trial simulation support this frozen candidate. The all-positive choice maximizes total estimated
value under the current unconstrained economics; it is not evidence that ranking is irrelevant.

Evidence artifacts:
{evidence}

## Uncertainty summary

The paired bootstrap report found positive value under the base synthetic assumptions, but
offline uncertainty cannot replace a prospective experiment. Because all-positive treats every
eligible user, a matched-random ranking comparison is not meaningful.

## Sensitivity summary

The selected policy is sensitive to conversion value, treatment cost, budget, and capacity.
All-positive winning with no constraints mostly reflects broad treatment profitability. Ranking
quality becomes materially more important under constrained treatment capacity or budget.

## Pre-registration and recommended validation trial

- Pre-registration: `{config.experiment_preregistration_path}`
- Recommended trial: {config.recommended_trial_design}
- Do not activate production treatment until the pre-registered randomized trial meets its
  efficacy, value, ROI, and guardrail decision rules.

## Known limitations

{_bullet_list(config.limitations)}

## Ethical and business risks

- Broad treatment can impose user burden, fatigue, or unequal exposure even when average value is
  positive.
- Historical features and channel availability can proxy for access or demographic differences.
- Conversion value assumptions can prioritize short-term revenue over user welfare.
- Segment-level impact and treatment burden must be reviewed before launch.

## Operational risks

- Schema drift, unseen categories, stale features, duplicate users, or changed intervention cost
  can invalidate scores.
- A model artifact without matching configuration and fingerprints must not be used.
- Batch recommendations require idempotent delivery and auditable treatment logs.

## Deployment checklist

- [ ] Reproduce dataset and config fingerprints.
- [ ] Verify required input schema and batch row uniqueness.
- [ ] Freeze policy version, economics, eligibility rule, and randomization design.
- [ ] Run and analyze the pre-registered real-world randomized validation.
- [ ] Confirm all efficacy, value, ROI, fairness, and operational guardrails.
- [ ] Approve ownership, treatment logging, incident response, and rollback procedures.

## Rollback criteria

Disable recommendations if input validation fails, fingerprints do not match the approved bundle,
conversion lift or net value breaches a registered guardrail, treatment cost exceeds its limit,
material segment harm appears, or the delivered intervention differs from the frozen treatment
definition.
"""


def generate_policy_card(
    config: PolicyDecisionConfig,
    dataset_fingerprint: DatasetFingerprint,
    config_fingerprint: str,
    output_path: Path | str,
) -> Path:
    """Write the Markdown policy card."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_policy_card(config, dataset_fingerprint, config_fingerprint),
        encoding="utf-8",
    )
    return destination
