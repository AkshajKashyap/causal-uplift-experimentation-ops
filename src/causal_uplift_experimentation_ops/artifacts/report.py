"""Freeze the selected policy bundle and generate audit reports."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from causal_uplift_experimentation_ops.artifacts.batch_score import (
    write_batch_scores,
)
from causal_uplift_experimentation_ops.artifacts.model_bundle import (
    FrozenPolicyArtifact,
    freeze_policy_bundle,
    refresh_policy_manifest,
)
from causal_uplift_experimentation_ops.artifacts.policy_card import (
    PolicyDecisionConfig,
    generate_policy_card,
)
from causal_uplift_experimentation_ops.data.validation import validate_experiment_data

DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_ARTIFACT_DIRECTORY = Path("artifacts/policy_bundle")
DEFAULT_POLICY_CARD_PATH = Path("reports/policy_card.md")
DEFAULT_MANIFEST_REPORT_PATH = Path("reports/policy_artifact_manifest.md")


@dataclass(frozen=True)
class PolicyArtifactResult:
    """Paths and fingerprints produced by the artifact-generation workflow."""

    frozen_artifact: FrozenPolicyArtifact
    batch_scores_path: Path
    policy_card_path: Path
    manifest_report_path: Path
    manifest: dict[str, object]


def render_manifest_report(
    artifact_directory: Path | str,
    manifest: dict[str, object],
) -> str:
    """Render file hashes, fingerprints, and reproduction commands."""
    artifact_files = manifest["artifact_files"]
    if not isinstance(artifact_files, dict):
        raise ValueError("Manifest artifact_files must be a mapping")
    file_rows = "\n".join(
        f"| `{Path(artifact_directory) / relative_path}` | `{digest}` |"
        for relative_path, digest in sorted(artifact_files.items())
    )
    dataset = manifest["dataset_fingerprint"]
    if not isinstance(dataset, dict):
        raise ValueError("Manifest dataset_fingerprint must be a mapping")
    return f"""# Policy Artifact Manifest

## Frozen artifact

- Artifact directory: `{artifact_directory}`
- Artifact version: **{manifest["artifact_version"]}**
- Package version: **{manifest["package_version"]}**
- Created: {manifest["creation_timestamp"]}
- Data rows: {int(dataset["rows"]):,}
- Data columns: {int(dataset["columns_count"])}
- Dataset fingerprint: `{dataset["fingerprint"]}`
- Dataset content SHA-256: `{dataset["content_sha256"]}`
- Feature contract fingerprint: `{manifest["feature_columns_fingerprint"]}`
- Policy config fingerprint: `{manifest["config_fingerprint"]}`

## Artifact files

| File | SHA-256 |
| --- | --- |
{file_rows}

`manifest.json` is intentionally excluded from its own file-hash map.

## Reproduction

From the repository root:

```bash
generate-synthetic-experiment --rows 10000 --seed 42
generate-experiment-planning
generate-policy-artifact --artifact-version {manifest["artifact_version"]} --seed 42
```

Run the batch scorer independently:

```bash
score-policy-batch \\
  --bundle artifacts/policy_bundle \\
  --input data/processed/synthetic_experiment.csv \\
  --output artifacts/policy_bundle/batch_scores.csv
```

## Audit warning

This artifact is a reproducible offline decision package, not production approval. Training,
evaluation, prospective simulation, and smoke-test scoring use synthetic data. Real-world
randomized validation under the frozen pre-registration is required before serving or treatment
delivery.
"""


def generate_manifest_report(
    artifact_directory: Path | str,
    manifest: dict[str, object],
    output_path: Path | str,
) -> Path:
    """Write the human-readable artifact manifest report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_manifest_report(artifact_directory, manifest),
        encoding="utf-8",
    )
    return destination


def generate_policy_artifact(
    data: pd.DataFrame,
    *,
    artifact_directory: Path | str = DEFAULT_ARTIFACT_DIRECTORY,
    policy_card_path: Path | str = DEFAULT_POLICY_CARD_PATH,
    manifest_report_path: Path | str = DEFAULT_MANIFEST_REPORT_PATH,
    artifact_version: str = "1.0.0",
    seed: int = 42,
    value_per_conversion: float = 100.0,
    treatment_cost_per_user: float = 1.0,
    capacity_fraction: float | None = None,
    budget: float | None = None,
) -> PolicyArtifactResult:
    """Train, freeze, smoke-test, and report the selected policy package."""
    config = PolicyDecisionConfig(
        artifact_version=artifact_version,
        value_per_conversion=value_per_conversion,
        treatment_cost_per_user=treatment_cost_per_user,
        capacity_fraction=capacity_fraction,
        budget=budget,
        random_seed=seed,
    )
    frozen = freeze_policy_bundle(data, artifact_directory, config=config)
    batch_scores_path = Path(artifact_directory) / "batch_scores.csv"
    write_batch_scores(
        data,
        frozen.artifact_directory,
        batch_scores_path,
    )
    _, manifest = refresh_policy_manifest(frozen.artifact_directory)
    card_path = generate_policy_card(
        frozen.bundle.config,
        frozen.dataset_fingerprint,
        frozen.config_fingerprint,
        policy_card_path,
    )
    artifact_manifest_path = generate_manifest_report(
        frozen.artifact_directory,
        manifest,
        manifest_report_path,
    )
    return PolicyArtifactResult(
        frozen_artifact=frozen,
        batch_scores_path=batch_scores_path,
        policy_card_path=card_path,
        manifest_report_path=artifact_manifest_path,
        manifest=manifest,
    )


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument(
        "--artifact-directory",
        type=Path,
        default=DEFAULT_ARTIFACT_DIRECTORY,
    )
    parser.add_argument("--policy-card", type=Path, default=DEFAULT_POLICY_CARD_PATH)
    parser.add_argument(
        "--manifest-report",
        type=Path,
        default=DEFAULT_MANIFEST_REPORT_PATH,
    )
    parser.add_argument("--artifact-version", default="1.0.0")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--value-per-conversion", type=float, default=100.0)
    parser.add_argument("--treatment-cost", type=float, default=1.0)
    parser.add_argument("--capacity-fraction", type=float)
    parser.add_argument("--budget", type=float)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate the selected policy's complete offline decision package."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    validate_experiment_data(data)
    result = generate_policy_artifact(
        data,
        artifact_directory=options.artifact_directory,
        policy_card_path=options.policy_card,
        manifest_report_path=options.manifest_report,
        artifact_version=options.artifact_version,
        seed=options.seed,
        value_per_conversion=options.value_per_conversion,
        treatment_cost_per_user=options.treatment_cost,
        capacity_fraction=options.capacity_fraction,
        budget=options.budget,
    )
    print(f"Wrote policy bundle to {result.frozen_artifact.artifact_directory}")
    print(f"Wrote batch scoring smoke test to {result.batch_scores_path}")
    print(f"Wrote policy card to {result.policy_card_path}")
    print(f"Wrote artifact manifest report to {result.manifest_report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
