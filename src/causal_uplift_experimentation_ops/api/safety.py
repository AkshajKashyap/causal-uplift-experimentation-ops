"""Staging authentication, audit logging, and in-memory operational metrics."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


def _environment_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _environment_int(name: str, default: int | None) -> int | None:
    value = os.getenv(name)
    return default if value is None else int(value)


def _environment_float(name: str, default: float | None) -> float | None:
    value = os.getenv(name)
    return default if value is None else float(value)


@dataclass(frozen=True)
class StagingAPIConfig:
    """Local safety settings, optionally populated from environment variables."""

    require_api_key: bool = False
    api_key_env_var: str = "CAUSAL_UPLIFT_API_KEY"
    max_batch_size: int = 1_000
    enable_audit_log: bool = False
    audit_log_path: Path = Path("artifacts/api_audit_log.jsonl")
    enable_budget_guardrail: bool = True
    max_recommendations_per_run: int | None = 1_000
    max_treatment_cost_per_run: float | None = 1_000.0
    default_treatment_cost_per_user: float = 1.0
    environment: str = "local-staging"

    def __post_init__(self) -> None:
        if not self.api_key_env_var.strip():
            raise ValueError("api_key_env_var must not be empty")
        if self.max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
        if (
            self.max_recommendations_per_run is not None
            and self.max_recommendations_per_run < 0
        ):
            raise ValueError("max_recommendations_per_run must be non-negative")
        if (
            self.max_treatment_cost_per_run is not None
            and self.max_treatment_cost_per_run < 0
        ):
            raise ValueError("max_treatment_cost_per_run must be non-negative")
        if self.default_treatment_cost_per_user < 0:
            raise ValueError("default_treatment_cost_per_user must be non-negative")
        if not self.environment.strip():
            raise ValueError("environment must not be empty")

    @classmethod
    def from_environment(cls) -> StagingAPIConfig:
        """Load supported safety controls from ``CAUSAL_UPLIFT_*`` variables."""
        return cls(
            require_api_key=_environment_bool(
                "CAUSAL_UPLIFT_REQUIRE_API_KEY",
                False,
            ),
            api_key_env_var=os.getenv(
                "CAUSAL_UPLIFT_API_KEY_ENV_VAR",
                "CAUSAL_UPLIFT_API_KEY",
            ),
            max_batch_size=int(
                _environment_int("CAUSAL_UPLIFT_MAX_BATCH_SIZE", 1_000)
            ),
            enable_audit_log=_environment_bool(
                "CAUSAL_UPLIFT_ENABLE_AUDIT_LOG",
                False,
            ),
            audit_log_path=Path(
                os.getenv(
                    "CAUSAL_UPLIFT_AUDIT_LOG_PATH",
                    "artifacts/api_audit_log.jsonl",
                )
            ),
            enable_budget_guardrail=_environment_bool(
                "CAUSAL_UPLIFT_ENABLE_BUDGET_GUARDRAIL",
                True,
            ),
            max_recommendations_per_run=_environment_int(
                "CAUSAL_UPLIFT_MAX_RECOMMENDATIONS_PER_RUN",
                1_000,
            ),
            max_treatment_cost_per_run=_environment_float(
                "CAUSAL_UPLIFT_MAX_TREATMENT_COST_PER_RUN",
                1_000.0,
            ),
            default_treatment_cost_per_user=float(
                _environment_float(
                    "CAUSAL_UPLIFT_DEFAULT_TREATMENT_COST_PER_USER",
                    1.0,
                )
            ),
            environment=os.getenv(
                "CAUSAL_UPLIFT_ENVIRONMENT",
                "local-staging",
            ),
        )


class JSONLAuditLogger:
    """Append bounded, feature-free events to a local JSONL file."""

    def __init__(self, enabled: bool, path: Path | str) -> None:
        self.enabled = enabled
        self.path = Path(path)
        self._lock = threading.Lock()

    def write(self, event: dict[str, object]) -> None:
        """Write one event atomically within this process."""
        if not self.enabled:
            return
        safe_event = {
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(safe_event, sort_keys=True) + "\n")


class OperationalMetrics:
    """Thread-safe process-local counters and latency aggregation."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_score_requests = 0
        self.total_batch_requests = 0
        self.total_users_scored = 0
        self.total_recommendations = 0
        self.total_errors = 0
        self.total_latency_ms = 0.0
        self.measured_requests = 0

    def record(
        self,
        *,
        endpoint: str,
        users_scored: int,
        recommendations: int,
        latency_ms: float,
        is_error: bool,
    ) -> None:
        """Record one attempted score or score-batch request."""
        with self._lock:
            if endpoint == "/score":
                self.total_score_requests += 1
            elif endpoint == "/score-batch":
                self.total_batch_requests += 1
            self.total_users_scored += users_scored
            self.total_recommendations += recommendations
            self.total_errors += int(is_error)
            self.total_latency_ms += latency_ms
            self.measured_requests += 1

    def snapshot(
        self,
        *,
        artifact_version: str,
        model_name: str,
        policy_name: str,
    ) -> dict[str, object]:
        """Return a stable JSON-compatible metrics snapshot."""
        with self._lock:
            mean_latency = (
                self.total_latency_ms / self.measured_requests
                if self.measured_requests
                else 0.0
            )
            return {
                "total_score_requests": self.total_score_requests,
                "total_batch_requests": self.total_batch_requests,
                "total_users_scored": self.total_users_scored,
                "total_recommendations": self.total_recommendations,
                "total_errors": self.total_errors,
                "mean_latency_ms": mean_latency,
                "artifact_version": artifact_version,
                "model_name": model_name,
                "policy_name": policy_name,
            }
