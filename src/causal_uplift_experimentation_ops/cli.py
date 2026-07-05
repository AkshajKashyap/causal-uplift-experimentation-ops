"""Package metadata and project-orientation command line interface."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from causal_uplift_experimentation_ops._version import package_version

PACKAGE_NAME = "causal-uplift-experimentation-ops"
PROJECT_SUMMARY = (
    "Reproducible causal ML workflow for randomized experiments, uplift "
    "evaluation, treatment policy simulation, and staging operations."
)
DEFAULT_ARTIFACT_DIRECTORY = Path("artifacts/policy_bundle")
KEY_CLI_COMMANDS = (
    "generate-synthetic-experiment",
    "generate-ab-report",
    "generate-crossfit-comparison",
    "generate-policy-artifact",
    "score-policy-batch",
    "serve-policy-api",
    "generate-staging-observability",
)
LIMITATIONS = (
    "Model and policy validation use synthetic data only.",
    "The FastAPI service is local/staging infrastructure, not a production deployment.",
    "Artifact promotion is currently held pending real prospective randomized validation.",
)


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def project_info(
    artifact_directory: Path | str = DEFAULT_ARTIFACT_DIRECTORY,
) -> dict[str, object]:
    """Return package, selected-policy, command, and limitation metadata."""
    directory = Path(artifact_directory)
    config = _read_json(directory / "policy_config.json")
    manifest = _read_json(directory / "manifest.json")
    return {
        "package_name": PACKAGE_NAME,
        "version": package_version(),
        "project_summary": PROJECT_SUMMARY,
        "selected_model": config.get("model_name", "logistic_s_learner"),
        "selected_policy": config.get("policy_name", "all_positive_uplift"),
        "artifact_version": manifest.get(
            "artifact_version",
            config.get("artifact_version", "not generated"),
        ),
        "promotion_status": "hold",
        "key_cli_commands": KEY_CLI_COMMANDS,
        "limitations": LIMITATIONS,
    }


def render_project_info(values: dict[str, object]) -> str:
    """Render project metadata for a terminal-oriented portfolio overview."""
    commands = "\n".join(
        f"  - {command}" for command in values["key_cli_commands"]
    )
    limitations = "\n".join(
        f"  - {limitation}" for limitation in values["limitations"]
    )
    return f"""Package: {values["package_name"]}
Version: {values["version"]}
Summary: {values["project_summary"]}
Selected model: {values["selected_model"]}
Selected policy: {values["selected_policy"]}
Artifact version: {values["artifact_version"]}
Promotion status: {values["promotion_status"]}
Key CLI commands:
{commands}
Limitations:
{limitations}"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="causal-uplift-ops",
        description=PROJECT_SUMMARY,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
    )
    subparsers = parser.add_subparsers(dest="command")
    info_parser = subparsers.add_parser(
        "project-info",
        help="Show the frozen policy selection, key commands, and limitations.",
    )
    info_parser.add_argument(
        "--artifact-directory",
        type=Path,
        default=DEFAULT_ARTIFACT_DIRECTORY,
    )
    return parser


def main(args: Sequence[str] | None = None) -> int:
    """Run the package metadata CLI."""
    parser = _build_parser()
    options = parser.parse_args(args)
    if options.command == "project-info":
        print(render_project_info(project_info(options.artifact_directory)))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
