"""Artifact-backed inference service with no training responsibilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from causal_uplift_experimentation_ops.api.errors import (
    ArtifactLoadError,
    PolicyServiceInputError,
)
from causal_uplift_experimentation_ops.api.schemas import (
    ManifestResponse,
    PolicyResponse,
    ScoreResponse,
    UserFeatures,
    VersionResponse,
)
from causal_uplift_experimentation_ops.artifacts.batch_score import (
    score_policy_batch,
)
from causal_uplift_experimentation_ops.artifacts.manifest import (
    load_manifest,
    package_version,
)
from causal_uplift_experimentation_ops.artifacts.model_bundle import (
    PersistedPolicyBundle,
    load_policy_bundle,
)
from causal_uplift_experimentation_ops.artifacts.policy_card import (
    PolicyDecisionConfig,
    load_policy_config,
)

DEFAULT_ARTIFACT_PATH = Path("artifacts/policy_bundle")
REQUIRED_ARTIFACT_FILES = (
    "model.joblib",
    "policy_config.json",
    "manifest.json",
    "feature_columns.json",
    "value_assumptions.json",
)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactLoadError(f"Could not load artifact metadata: {path}") from error


class PolicyInferenceService:
    """Load one frozen policy bundle and expose safe scoring operations."""

    def __init__(
        self,
        artifact_path: Path | str = DEFAULT_ARTIFACT_PATH,
        max_batch_size: int = 1_000,
    ) -> None:
        if max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
        self.artifact_path = Path(artifact_path)
        self.max_batch_size = max_batch_size
        self.bundle: PersistedPolicyBundle
        self.config: PolicyDecisionConfig
        self.manifest: dict[str, object]
        self.feature_columns: tuple[str, ...]
        self.value_assumptions: dict[str, object]
        self._load_artifact()

    def _load_artifact(self) -> None:
        missing = [
            filename
            for filename in REQUIRED_ARTIFACT_FILES
            if not (self.artifact_path / filename).is_file()
        ]
        if missing:
            raise ArtifactLoadError(
                f"Policy artifact bundle is missing required files at "
                f"{self.artifact_path}: {', '.join(missing)}"
            )
        try:
            self.bundle = load_policy_bundle(self.artifact_path)
            self.config = load_policy_config(self.artifact_path)
            self.manifest = load_manifest(self.artifact_path)
        except (ValueError, OSError) as error:
            raise ArtifactLoadError(f"Could not load policy artifact: {error}") from error

        feature_values = _load_json(self.artifact_path / "feature_columns.json")
        value_assumptions = _load_json(self.artifact_path / "value_assumptions.json")
        if not isinstance(feature_values, list) or not all(
            isinstance(value, str) for value in feature_values
        ):
            raise ArtifactLoadError("feature_columns.json must contain a list of strings")
        if not isinstance(value_assumptions, dict):
            raise ArtifactLoadError("value_assumptions.json must contain an object")
        self.feature_columns = tuple(feature_values)
        self.value_assumptions = value_assumptions

        if self.feature_columns != self.config.selected_feature_columns:
            raise ArtifactLoadError("Feature metadata does not match the frozen policy config")
        if self.bundle.config.to_dict() != self.config.to_dict():
            raise ArtifactLoadError("Serialized model config does not match policy_config.json")
        manifest_config_fingerprint = self.manifest.get("config_fingerprint")
        if not isinstance(manifest_config_fingerprint, str):
            raise ArtifactLoadError("Manifest config fingerprint is missing")

    @property
    def version(self) -> VersionResponse:
        """Return safe package and artifact identity metadata."""
        dataset = self.manifest.get("dataset_fingerprint")
        if not isinstance(dataset, dict) or "fingerprint" not in dataset:
            raise ArtifactLoadError("Manifest dataset fingerprint is missing")
        return VersionResponse(
            package_version=package_version(),
            artifact_version=self.config.artifact_version,
            model_name=self.config.model_name,
            policy_name=self.config.policy_name,
            dataset_fingerprint=str(dataset["fingerprint"]),
            config_fingerprint=str(self.manifest["config_fingerprint"]),
        )

    @property
    def policy_summary(self) -> PolicyResponse:
        """Return the intended use and frozen decision without model internals."""
        return PolicyResponse(
            artifact_version=self.config.artifact_version,
            model_name=self.config.model_name,
            policy_name=self.config.policy_name,
            policy_rule=self.config.policy_rule,
            selected_feature_columns=list(self.feature_columns),
            intended_use=self.config.intended_use,
            out_of_scope_use=self.config.out_of_scope_use,
            limitations=list(self.config.limitations),
            value_assumptions=self.value_assumptions,
            recommended_trial_design=self.config.recommended_trial_design,
        )

    @property
    def manifest_summary(self) -> ManifestResponse:
        """Return a bounded manifest view containing only audit metadata."""
        dataset = self.manifest.get("dataset_fingerprint")
        artifact_files = self.manifest.get("artifact_files")
        if not isinstance(dataset, dict) or not isinstance(artifact_files, dict):
            raise ArtifactLoadError("Artifact manifest metadata is invalid")
        return ManifestResponse(
            manifest_version=str(self.manifest["manifest_version"]),
            artifact_version=str(self.manifest["artifact_version"]),
            package_version=str(self.manifest["package_version"]),
            creation_timestamp=str(self.manifest["creation_timestamp"]),
            dataset_fingerprint=str(dataset["fingerprint"]),
            dataset_rows=int(dataset["rows"]),
            dataset_columns=int(dataset["columns_count"]),
            feature_columns_fingerprint=str(
                self.manifest["feature_columns_fingerprint"]
            ),
            config_fingerprint=str(self.manifest["config_fingerprint"]),
            artifact_files=sorted(str(filename) for filename in artifact_files),
        )

    def score_users(self, users: list[UserFeatures]) -> list[ScoreResponse]:
        """Score a bounded request with the shared artifact batch-scoring path."""
        if not users:
            raise PolicyServiceInputError("Batch request must contain at least one user")
        if len(users) > self.max_batch_size:
            raise PolicyServiceInputError(
                f"Batch request exceeds maximum size of {self.max_batch_size}"
            )
        frame = pd.DataFrame([user.model_dump() for user in users])
        try:
            scores = score_policy_batch(frame, self.bundle)
        except ValueError as error:
            raise PolicyServiceInputError(str(error)) from error
        return [
            ScoreResponse(
                user_id=int(row.user_id),
                predicted_uplift=float(row.predicted_uplift),
                predicted_control_conversion=float(
                    row.predicted_control_conversion
                ),
                predicted_treatment_conversion=float(
                    row.predicted_treatment_conversion
                ),
                recommended_treatment=int(row.recommended_treatment),
                policy_eligible=bool(row.policy_eligible),
                policy_name=str(row.policy_name),
                model_name=str(row.model_name),
                artifact_version=str(row.artifact_version),
                reason=self.config.policy_rule,
            )
            for row in scores.itertuples(index=False)
        ]

    def score_user(self, user: UserFeatures) -> ScoreResponse:
        """Score one user through the same deterministic batch path."""
        return self.score_users([user])[0]
