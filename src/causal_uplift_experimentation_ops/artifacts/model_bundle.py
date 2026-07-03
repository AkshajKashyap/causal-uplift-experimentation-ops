"""Train, persist, load, and audit the selected uplift policy bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import joblib
import pandas as pd

from causal_uplift_experimentation_ops.artifacts.manifest import (
    DatasetFingerprint,
    fingerprint_config,
    fingerprint_dataset,
    load_manifest,
    write_manifest,
)
from causal_uplift_experimentation_ops.artifacts.policy_card import (
    PolicyDecisionConfig,
    load_policy_config,
)
from causal_uplift_experimentation_ops.evaluation.splitting import (
    resolve_feature_columns,
)
from causal_uplift_experimentation_ops.models.s_learner import LogisticSLearner

MODEL_FILENAME = "model.joblib"


@dataclass(frozen=True)
class PersistedPolicyBundle:
    """Serializable fitted model plus its exact decision configuration."""

    model: LogisticSLearner
    config: PolicyDecisionConfig


@dataclass(frozen=True)
class FrozenPolicyArtifact:
    """Paths, hashes, and in-memory objects created while freezing a policy."""

    artifact_directory: Path
    model_path: Path
    config_path: Path
    manifest_path: Path
    feature_columns_path: Path
    value_assumptions_path: Path
    readme_path: Path
    bundle: PersistedPolicyBundle
    dataset_fingerprint: DatasetFingerprint
    config_fingerprint: str
    manifest: dict[str, object]


def _artifact_readme(config: PolicyDecisionConfig) -> str:
    return f"""# Frozen Policy Bundle

This directory contains artifact version `{config.artifact_version}` for
`{config.model_name}` with policy `{config.policy_name}`.

Files:

- `model.joblib`: fitted Logistic S-learner and frozen decision configuration
- `policy_config.json`: policy, evidence, economics, use, and limitation contract
- `manifest.json`: data, feature, config, package, and artifact-file fingerprints
- `feature_columns.json`: ordered required input features
- `value_assumptions.json`: conversion value, treatment cost, capacity, and budget
- `batch_scores.csv`: generated smoke-test scores; excluded from source control

Reproduce from the repository root:

```bash
generate-synthetic-experiment
generate-policy-artifact
```

Score another compatible CSV:

```bash
score-policy-batch --bundle artifacts/policy_bundle --input path/to/input.csv
```

This bundle is validated only on synthetic data. It must not trigger production treatment until
the pre-registered real-world randomized validation passes.
"""


def freeze_policy_bundle(
    data: pd.DataFrame,
    artifact_directory: Path | str,
    config: PolicyDecisionConfig | None = None,
) -> FrozenPolicyArtifact:
    """Fit the selected full-data S-learner and persist an auditable bundle."""
    directory = Path(artifact_directory)
    directory.mkdir(parents=True, exist_ok=True)
    base_config = config or PolicyDecisionConfig()
    if base_config.model_name != "logistic_s_learner":
        raise ValueError("Only 'logistic_s_learner' is supported by this policy bundle")
    if base_config.policy_name != "all_positive_uplift":
        raise ValueError("Only 'all_positive_uplift' is supported by this policy bundle")

    features = resolve_feature_columns(
        data,
        feature_columns=base_config.selected_feature_columns,
    )
    dataset_fingerprint = fingerprint_dataset(data)
    frozen_config = replace(
        base_config,
        selected_feature_columns=features,
        training_data_fingerprint=dataset_fingerprint.fingerprint,
    )
    model = LogisticSLearner(features, seed=frozen_config.random_seed)
    model.fit(data)
    bundle = PersistedPolicyBundle(model=model, config=frozen_config)

    model_path = directory / MODEL_FILENAME
    config_path = directory / "policy_config.json"
    feature_columns_path = directory / "feature_columns.json"
    value_assumptions_path = directory / "value_assumptions.json"
    readme_path = directory / "README.md"
    joblib.dump(bundle, model_path)
    config_path.write_text(
        json.dumps(frozen_config.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    feature_columns_path.write_text(
        json.dumps(list(features), indent=2) + "\n",
        encoding="utf-8",
    )
    value_assumptions_path.write_text(
        json.dumps(
            {
                "value_per_conversion": frozen_config.value_per_conversion,
                "treatment_cost_per_user": frozen_config.treatment_cost_per_user,
                "capacity_fraction": frozen_config.capacity_fraction,
                "budget": frozen_config.budget,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    readme_path.write_text(_artifact_readme(frozen_config), encoding="utf-8")

    config_hash = fingerprint_config(frozen_config)
    manifest_path, manifest = write_manifest(
        directory,
        artifact_version=frozen_config.artifact_version,
        creation_timestamp=frozen_config.creation_timestamp,
        dataset_fingerprint=dataset_fingerprint,
        feature_columns=features,
        config_fingerprint=config_hash,
    )
    return FrozenPolicyArtifact(
        artifact_directory=directory,
        model_path=model_path,
        config_path=config_path,
        manifest_path=manifest_path,
        feature_columns_path=feature_columns_path,
        value_assumptions_path=value_assumptions_path,
        readme_path=readme_path,
        bundle=bundle,
        dataset_fingerprint=dataset_fingerprint,
        config_fingerprint=config_hash,
        manifest=manifest,
    )


def load_policy_bundle(artifact_directory: Path | str) -> PersistedPolicyBundle:
    """Load and minimally validate the serialized policy bundle."""
    path = Path(artifact_directory) / MODEL_FILENAME
    if not path.exists():
        raise ValueError(f"Policy model bundle not found: {path}")
    bundle = joblib.load(path)
    if not isinstance(bundle, PersistedPolicyBundle):
        raise ValueError("Serialized object is not a supported policy bundle")
    if not bundle.model.is_fitted:
        raise ValueError("Serialized policy model is not fitted")
    return bundle


def refresh_policy_manifest(
    artifact_directory: Path | str,
) -> tuple[Path, dict[str, object]]:
    """Refresh file hashes after optional batch smoke-test output is written."""
    directory = Path(artifact_directory)
    config = load_policy_config(directory)
    existing = load_manifest(directory)
    dataset_values = existing["dataset_fingerprint"]
    if not isinstance(dataset_values, dict):
        raise ValueError("Manifest dataset fingerprint is invalid")
    dataset_fingerprint = DatasetFingerprint(
        rows=int(dataset_values["rows"]),
        columns_count=int(dataset_values["columns_count"]),
        columns=tuple(dataset_values["columns"]),
        content_sha256=str(dataset_values["content_sha256"]),
        fingerprint=str(dataset_values["fingerprint"]),
    )
    return write_manifest(
        directory,
        artifact_version=config.artifact_version,
        creation_timestamp=config.creation_timestamp,
        dataset_fingerprint=dataset_fingerprint,
        feature_columns=config.selected_feature_columns,
        config_fingerprint=fingerprint_config(config),
    )
