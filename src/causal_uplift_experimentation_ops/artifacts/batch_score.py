"""Load a frozen policy bundle and produce production-style batch decisions."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from causal_uplift_experimentation_ops.artifacts.model_bundle import (
    PersistedPolicyBundle,
    load_policy_bundle,
)

DEFAULT_BUNDLE_PATH = Path("artifacts/policy_bundle")
DEFAULT_INPUT_PATH = Path("data/processed/synthetic_experiment.csv")
DEFAULT_OUTPUT_PATH = DEFAULT_BUNDLE_PATH / "batch_scores.csv"


def _maximum_recommended_users(
    row_count: int,
    bundle: PersistedPolicyBundle,
) -> int:
    config = bundle.config
    limits = [row_count]
    if config.capacity_fraction is not None:
        limits.append(int(np.floor(row_count * config.capacity_fraction)))
    if config.budget is not None and config.treatment_cost_per_user > 0:
        limits.append(
            int(np.floor(config.budget / config.treatment_cost_per_user))
        )
    return max(0, min(limits))


def score_policy_batch(
    data: pd.DataFrame,
    bundle: PersistedPolicyBundle,
    include_synthetic_debug: bool = False,
) -> pd.DataFrame:
    """Score potential outcomes and apply the frozen treatment rule."""
    if "user_id" not in data:
        raise ValueError("Missing batch scoring columns: user_id")
    if data["user_id"].duplicated().any():
        raise ValueError("'user_id' must be unique for batch scoring")
    missing_features = sorted(
        set(bundle.config.selected_feature_columns) - set(data.columns)
    )
    if missing_features:
        raise ValueError(f"Missing feature columns: {', '.join(missing_features)}")

    scoring_data = data.copy()
    if "treatment" not in scoring_data:
        scoring_data["treatment"] = 0
    if "conversion" not in scoring_data:
        scoring_data["conversion"] = 0
    predictions = bundle.model.predict(scoring_data)
    if bundle.config.policy_rule != "predicted_uplift > 0":
        raise ValueError(f"Unsupported policy rule: {bundle.config.policy_rule}")

    eligible = predictions["predicted_uplift"] > 0
    maximum_users = _maximum_recommended_users(len(data), bundle)
    ranked_eligible = predictions.loc[eligible].sort_values(
        "predicted_uplift",
        ascending=False,
        kind="mergesort",
    )
    recommended_ids = set(
        ranked_eligible.head(maximum_users)["user_id"].tolist()
    )
    output = predictions.loc[
        :,
        [
            "user_id",
            "predicted_control_conversion",
            "predicted_treatment_conversion",
            "predicted_uplift",
        ],
    ].copy()
    output["policy_eligible"] = eligible.to_numpy()
    output["recommended_treatment"] = output["user_id"].isin(recommended_ids).astype(
        int
    )
    output["policy_name"] = bundle.config.policy_name
    output["model_name"] = bundle.config.model_name
    output["artifact_version"] = bundle.config.artifact_version
    if include_synthetic_debug and "true_uplift" in data:
        output["synthetic_debug_true_uplift"] = data["true_uplift"].to_numpy()
    return output


def write_batch_scores(
    data: pd.DataFrame,
    artifact_directory: Path | str,
    output_path: Path | str,
    include_synthetic_debug: bool = False,
) -> Path:
    """Load a bundle, score a DataFrame, and write decisions to CSV."""
    scores = score_policy_batch(
        data,
        load_policy_bundle(artifact_directory),
        include_synthetic_debug=include_synthetic_debug,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(destination, index=False)
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE_PATH)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--include-synthetic-debug", action="store_true")
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Score an input CSV with the frozen policy bundle."""
    options = _parse_args(args)
    data = pd.read_csv(options.input)
    output = write_batch_scores(
        data,
        options.bundle,
        options.output,
        include_synthetic_debug=options.include_synthetic_debug,
    )
    print(f"Wrote {len(data):,} batch policy scores to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
