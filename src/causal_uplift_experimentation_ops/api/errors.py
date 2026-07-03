"""Domain errors exposed by the staging policy API."""


class ArtifactLoadError(RuntimeError):
    """Raised when the frozen policy artifact cannot be loaded safely."""


class PolicyServiceInputError(ValueError):
    """Raised when a syntactically valid request cannot be scored."""


class AuthenticationError(PermissionError):
    """Raised when staging API-key authentication fails."""


class GuardrailValidationError(PolicyServiceInputError):
    """Raised when request-level budget controls are inconsistent."""


class PolicyScoringError(RuntimeError):
    """Raised when a valid request cannot be scored by the frozen model."""
