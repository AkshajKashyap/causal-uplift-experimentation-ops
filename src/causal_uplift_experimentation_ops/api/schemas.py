"""Pydantic request and response contracts for staging policy inference."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserFeatures(BaseModel):
    """Pre-treatment features required by the frozen synthetic policy."""

    model_config = ConfigDict(extra="forbid")

    user_id: int
    age: int = Field(ge=18, le=120)
    prior_purchases: int = Field(ge=0)
    avg_order_value: float = Field(gt=0)
    days_since_last_purchase: int = Field(ge=0)
    channel: str = Field(min_length=1)


class ScoreResponse(BaseModel):
    """Auditable potential-outcome predictions and policy decision."""

    user_id: int
    predicted_uplift: float
    predicted_control_conversion: float
    predicted_treatment_conversion: float
    recommended_treatment: int
    policy_eligible: bool
    policy_name: str
    model_name: str
    artifact_version: str
    reason: str


class BatchScoreRequest(BaseModel):
    """A bounded list is enforced by the service for clear 400 errors."""

    model_config = ConfigDict(extra="forbid")

    users: list[UserFeatures]


class BatchScoreResponse(BaseModel):
    """Batch size plus one deterministic result per requested user."""

    batch_size: int
    scores: list[ScoreResponse]


class HealthResponse(BaseModel):
    """Liveness and artifact readiness without model internals."""

    status: str
    artifact_loaded: bool
    service: str
    artifact_version: str | None = None
    model_name: str | None = None
    policy_name: str | None = None
    detail: str | None = None


class VersionResponse(BaseModel):
    """Package, artifact, model, policy, and fingerprint versions."""

    package_version: str
    artifact_version: str
    model_name: str
    policy_name: str
    dataset_fingerprint: str
    config_fingerprint: str


class PolicyResponse(BaseModel):
    """Safe summary of the frozen decision contract."""

    artifact_version: str
    model_name: str
    policy_name: str
    policy_rule: str
    selected_feature_columns: list[str]
    intended_use: str
    out_of_scope_use: str
    limitations: list[str]
    value_assumptions: dict[str, Any]
    recommended_trial_design: str


class ManifestResponse(BaseModel):
    """Safe manifest metadata; binary contents and model internals are excluded."""

    manifest_version: str
    artifact_version: str
    package_version: str
    creation_timestamp: str
    dataset_fingerprint: str
    dataset_rows: int
    dataset_columns: int
    feature_columns_fingerprint: str
    config_fingerprint: str
    artifact_files: list[str]
