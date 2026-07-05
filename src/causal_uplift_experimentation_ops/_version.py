"""Installed package version with a source-tree fallback."""

from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "causal-uplift-experimentation-ops"


def package_version() -> str:
    """Return the version declared by the installed project metadata."""
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.1.0"
