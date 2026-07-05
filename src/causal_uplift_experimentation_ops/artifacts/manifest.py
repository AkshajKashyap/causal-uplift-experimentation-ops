"""Deterministic fingerprints and audit manifests for policy artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from causal_uplift_experimentation_ops._version import package_version


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data in a stable, hashable representation."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(value: bytes) -> str:
    """Return a hexadecimal SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path | str) -> str:
    """Hash a file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class DatasetFingerprint:
    """Shape, schema, content, and composite hashes for a training dataset."""

    rows: int
    columns_count: int
    columns: tuple[str, ...]
    content_sha256: str
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        result = asdict(self)
        result["columns"] = list(self.columns)
        return result


def fingerprint_dataset(data: pd.DataFrame) -> DatasetFingerprint:
    """Fingerprint ordered rows and columns using canonical CSV content."""
    columns = tuple(str(column) for column in data.columns)
    csv_content = data.to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    ).encode("utf-8")
    content_hash = sha256_bytes(csv_content)
    metadata = {
        "rows": len(data),
        "columns_count": len(columns),
        "columns": list(columns),
        "content_sha256": content_hash,
    }
    return DatasetFingerprint(
        rows=len(data),
        columns_count=len(columns),
        columns=columns,
        content_sha256=content_hash,
        fingerprint=sha256_bytes(canonical_json(metadata).encode("utf-8")),
    )


def fingerprint_feature_columns(feature_columns: tuple[str, ...]) -> str:
    """Hash an ordered feature-column contract."""
    return sha256_bytes(canonical_json(list(feature_columns)).encode("utf-8"))


def fingerprint_config(config: Mapping[str, object] | Any) -> str:
    """Hash decision configuration while excluding its wall-clock timestamp."""
    if hasattr(config, "to_dict"):
        values = config.to_dict()
    else:
        values = dict(config)
    stable_values = dict(values)
    stable_values.pop("creation_timestamp", None)
    return sha256_bytes(canonical_json(stable_values).encode("utf-8"))


def artifact_file_hashes(
    artifact_directory: Path | str,
    exclude: tuple[str, ...] = ("manifest.json",),
) -> dict[str, str]:
    """Return sorted relative-path hashes for files in an artifact directory."""
    directory = Path(artifact_directory)
    excluded = set(exclude)
    return {
        path.relative_to(directory).as_posix(): file_sha256(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name not in excluded
    }


def write_manifest(
    artifact_directory: Path | str,
    *,
    artifact_version: str,
    creation_timestamp: str,
    dataset_fingerprint: DatasetFingerprint,
    feature_columns: tuple[str, ...],
    config_fingerprint: str,
) -> tuple[Path, dict[str, object]]:
    """Create or refresh the artifact manifest after all files are present."""
    directory = Path(artifact_directory)
    manifest: dict[str, object] = {
        "manifest_version": "1.0",
        "artifact_version": artifact_version,
        "package_version": package_version(),
        "creation_timestamp": creation_timestamp,
        "dataset_fingerprint": dataset_fingerprint.to_dict(),
        "feature_columns": list(feature_columns),
        "feature_columns_fingerprint": fingerprint_feature_columns(feature_columns),
        "config_fingerprint": config_fingerprint,
        "artifact_files": artifact_file_hashes(directory),
    }
    destination = directory / "manifest.json"
    destination.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination, manifest


def load_manifest(artifact_directory: Path | str) -> dict[str, object]:
    """Load an artifact manifest."""
    path = Path(artifact_directory) / "manifest.json"
    if not path.exists():
        raise ValueError(f"Policy artifact manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
