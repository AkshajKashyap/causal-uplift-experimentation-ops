"""Domain errors exposed by the staging policy API."""


class ArtifactLoadError(RuntimeError):
    """Raised when the frozen policy artifact cannot be loaded safely."""


class PolicyServiceInputError(ValueError):
    """Raised when a syntactically valid request cannot be scored."""
