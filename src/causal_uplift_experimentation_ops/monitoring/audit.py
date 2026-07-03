"""Offline JSONL audit-log generation and operational analysis."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from causal_uplift_experimentation_ops.artifacts.manifest import load_manifest
from causal_uplift_experimentation_ops.artifacts.policy_card import load_policy_config
from causal_uplift_experimentation_ops.monitoring.drift import (
    threshold_severity,
    worst_severity,
)

DEFAULT_AUDIT_PATH = Path("artifacts/api_audit_log.jsonl")
DEFAULT_ARTIFACT_PATH = Path("artifacts/policy_bundle")


@dataclass(frozen=True)
class AuditLogSummary:
    """Aggregate counts, latency, identity sets, warnings, and status."""

    status: str
    metrics: dict[str, object]
    endpoint_request_counts: dict[str, int]
    endpoint_recommendation_counts: dict[str, int]
    warnings: tuple[str, ...] = ()


def analyze_audit_log(
    path: Path | str,
    *,
    error_rate_warn: float = 0.02,
    error_rate_fail: float = 0.05,
    p95_latency_warn_ms: float = 500.0,
    p95_latency_fail_ms: float = 1_000.0,
) -> AuditLogSummary:
    """Read feature-free API audit events and summarize operational health."""
    audit_path = Path(path)
    if not audit_path.exists():
        return AuditLogSummary(
            status="warn",
            metrics={
                "total_events": 0,
                "total_score_requests": 0,
                "total_batch_requests": 0,
                "total_users_scored": 0,
                "total_recommendations": 0,
                "total_errors": 0,
                "error_rate": 0.0,
                "mean_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "artifact_versions_seen": [],
                "model_names_seen": [],
                "policy_names_seen": [],
            },
            endpoint_request_counts={},
            endpoint_recommendation_counts={},
            warnings=(f"Audit log not found: {audit_path}",),
        )

    events: list[dict[str, object]] = []
    malformed_lines = 0
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed_lines += 1
            continue
        if isinstance(value, dict):
            events.append(value)
        else:
            malformed_lines += 1
    if not events:
        return AuditLogSummary(
            status="fail" if malformed_lines else "warn",
            metrics={
                "total_events": 0,
                "total_score_requests": 0,
                "total_batch_requests": 0,
                "total_users_scored": 0,
                "total_recommendations": 0,
                "total_errors": malformed_lines,
                "error_rate": 1.0 if malformed_lines else 0.0,
                "mean_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "artifact_versions_seen": [],
                "model_names_seen": [],
                "policy_names_seen": [],
            },
            endpoint_request_counts={},
            endpoint_recommendation_counts={},
            warnings=("Audit log contains no valid events.",),
        )

    endpoint_counts = Counter(str(event.get("endpoint", "unknown")) for event in events)
    endpoint_recommendations: Counter[str] = Counter()
    for event in events:
        endpoint_recommendations[str(event.get("endpoint", "unknown"))] += int(
            event.get("recommended_treatment_count") or 0
        )
    latencies = np.asarray(
        [float(event.get("latency_ms") or 0.0) for event in events],
        dtype=float,
    )
    total_errors = sum(event.get("status") == "error" for event in events)
    total_events = len(events)
    error_rate = total_errors / total_events
    error_severity = threshold_severity(
        error_rate,
        error_rate_warn,
        error_rate_fail,
    )
    p95_latency = float(np.quantile(latencies, 0.95))
    latency_severity = threshold_severity(
        p95_latency,
        p95_latency_warn_ms,
        p95_latency_fail_ms,
    )
    statuses = [error_severity, latency_severity]
    if malformed_lines:
        statuses.append("fail")
    warnings = []
    if malformed_lines:
        warnings.append(f"Ignored {malformed_lines} malformed audit line(s).")
    if error_severity != "pass":
        warnings.append(f"Audit error rate is {error_rate:.2%}.")
    if latency_severity != "pass":
        warnings.append(f"Audit p95 latency is {p95_latency:.2f} ms.")

    metrics: dict[str, object] = {
        "total_events": total_events,
        "total_score_requests": endpoint_counts.get("/score", 0),
        "total_batch_requests": endpoint_counts.get("/score-batch", 0),
        "total_users_scored": sum(int(event.get("batch_size") or 0) for event in events),
        "total_recommendations": sum(
            int(event.get("recommended_treatment_count") or 0)
            for event in events
        ),
        "total_errors": total_errors,
        "error_rate": error_rate,
        "mean_latency_ms": float(latencies.mean()),
        "p50_latency_ms": float(np.quantile(latencies, 0.50)),
        "p95_latency_ms": p95_latency,
        "max_latency_ms": float(latencies.max()),
        "artifact_versions_seen": sorted(
            {
                str(event["artifact_version"])
                for event in events
                if event.get("artifact_version") is not None
            }
        ),
        "model_names_seen": sorted(
            {
                str(event["model_name"])
                for event in events
                if event.get("model_name") is not None
            }
        ),
        "policy_names_seen": sorted(
            {
                str(event["policy_name"])
                for event in events
                if event.get("policy_name") is not None
            }
        ),
    }
    return AuditLogSummary(
        status=worst_severity(statuses),
        metrics=metrics,
        endpoint_request_counts=dict(sorted(endpoint_counts.items())),
        endpoint_recommendation_counts=dict(
            sorted(endpoint_recommendations.items())
        ),
        warnings=tuple(warnings),
    )


def generate_audit_smoke_log(
    output_path: Path | str = DEFAULT_AUDIT_PATH,
    artifact_path: Path | str = DEFAULT_ARTIFACT_PATH,
) -> Path:
    """Write deterministic, realistic, feature-free audit events."""
    manifest = load_manifest(artifact_path)
    config = load_policy_config(artifact_path)
    events = []
    specifications = (
        ("/score", 1, 1, 12.5, 0.045),
        ("/score", 1, 1, 11.2, 0.038),
        ("/score-batch", 3, 2, 24.8, 0.031),
        ("/score-batch", 5, 4, 31.4, 0.029),
        ("/score", 1, 1, 10.7, 0.052),
        ("/score-batch", 4, 3, 27.9, 0.034),
    )
    for index, (endpoint, batch_size, recommendations, latency, mean_uplift) in enumerate(
        specifications,
        start=1,
    ):
        events.append(
            {
                "timestamp": f"2026-01-01T00:00:{index:02d}+00:00",
                "endpoint": endpoint,
                "request_id": f"smoke-request-{index:03d}",
                "batch_size": batch_size,
                "artifact_version": manifest["artifact_version"],
                "model_name": config.model_name,
                "policy_name": config.policy_name,
                "recommended_treatment_count": recommendations,
                "mean_predicted_uplift": mean_uplift,
                "min_predicted_uplift": mean_uplift - 0.01,
                "max_predicted_uplift": mean_uplift + 0.01,
                "status": "success",
                "error_type": None,
                "latency_ms": latency,
            }
        )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_ARTIFACT_PATH)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate a deterministic audit-log smoke fixture."""
    options = _parse_args(args)
    output = generate_audit_smoke_log(options.output, options.bundle)
    print(f"Wrote API audit smoke log to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
