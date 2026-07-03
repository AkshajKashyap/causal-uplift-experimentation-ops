"""Generate documentation for staging API safety and operational controls."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from causal_uplift_experimentation_ops.api.safety import StagingAPIConfig
from causal_uplift_experimentation_ops.api.schemas import UserFeatures
from causal_uplift_experimentation_ops.api.service import (
    DEFAULT_ARTIFACT_PATH,
    PolicyInferenceService,
)

DEFAULT_REPORT_PATH = Path("reports/api_staging_safety_controls.md")
EXAMPLE_USERS = [
    UserFeatures(
        user_id=20001,
        age=35,
        prior_purchases=4,
        avg_order_value=82.5,
        days_since_last_purchase=21,
        channel="email",
    ),
    UserFeatures(
        user_id=20002,
        age=48,
        prior_purchases=2,
        avg_order_value=65.0,
        days_since_last_purchase=50,
        channel="organic",
    ),
    UserFeatures(
        user_id=20003,
        age=29,
        prior_purchases=1,
        avg_order_value=55.0,
        days_since_last_purchase=90,
        channel="social",
    ),
]


def render_safety_report(
    service: PolicyInferenceService,
    config: StagingAPIConfig,
) -> str:
    """Render authentication, audit, guardrail, and metrics behavior."""
    example = service.score_batch(
        EXAMPLE_USERS,
        request_id="example-budget-request",
        max_recommendations=1,
        treatment_cost_per_user=2.0,
    )
    example_json = json.dumps(example.model_dump(), indent=2)
    return f"""# Staging API Safety Controls

## Scope

These controls make local/staging inference safer and more auditable. They do not convert the
synthetic-only policy service into a production deployment.

## Controls added

- Optional `X-API-Key` authentication using a configured environment variable
- Per-request UUIDs returned in score bodies, errors, and `X-Request-ID` headers
- Feature-free JSONL audit events for every score and score-batch attempt
- Request-level and configured recommendation/cost limits
- Highest-uplift retention when recommendations must be suppressed
- Process-local request, user, recommendation, error, and latency metrics
- Consistent authentication, artifact, payload, guardrail, and scoring errors

## Authentication

Protected endpoints: `POST /score`, `POST /score-batch`, `GET /policy`, and `GET /manifest`.
`GET /health`, `GET /version`, and `GET /metrics` remain available without a key.

- Authentication required by default: **{config.require_api_key}**
- API-key environment variable: `{config.api_key_env_var}`
- Environment label: `{config.environment}`

The API key is compared with `secrets.compare_digest` and is never written to the audit log.

## Audit log

- Enabled by default: **{config.enable_audit_log}**
- Default path: `{config.audit_log_path}`

Each JSONL event contains:

```text
timestamp, endpoint, request_id, batch_size, artifact_version, model_name,
policy_name, recommended_treatment_count, mean_predicted_uplift,
min_predicted_uplift, max_predicted_uplift, status, error_type, latency_ms
```

Raw user features, API keys, treatment assignments, conversion, spend, and synthetic true uplift
are not logged.

## Budget and capacity behavior

- Guardrail enabled: **{config.enable_budget_guardrail}**
- Configured maximum recommendations per run: {config.max_recommendations_per_run}
- Configured maximum treatment cost per run: {config.max_treatment_cost_per_run}
- Default treatment cost per user: {config.default_treatment_cost_per_user}

The service first scores every user through the frozen artifact. If configured or request-level
limits bind, it ranks originally recommended users by predicted uplift and keeps the highest
scores. Suppressed users remain in the response with `recommended_treatment=0`.

## Example budget-limited batch response

```json
{example_json}
```

## Request IDs

Every HTTP response exposes `X-Request-ID`. Score and batch response bodies also include the same
ID. Error bodies include the request ID and a stable error type where practical.

## Operational metrics

`GET /metrics` returns:

```text
total_score_requests, total_batch_requests, total_users_scored,
total_recommendations, total_errors, mean_latency_ms,
artifact_version, model_name, policy_name
```

Metrics count attempted score endpoints. User and recommendation totals count successful scoring.

## Limitations

- In-memory metrics reset whenever the process restarts.
- The JSONL audit log is local only and has no rotation, retention, signing, or central ingestion.
- API-key authentication is staging-grade, not enterprise identity or authorization.
- Recommendation and cost limits are process/request local; there is no central budget store
  across workers or service instances.
- There is no rate limiting, durable idempotency store, distributed tracing, or production SLO.
- No production rollout is permitted without successful prospective randomized trial results.
"""


def generate_safety_report(
    artifact_path: Path | str = DEFAULT_ARTIFACT_PATH,
    output_path: Path | str = DEFAULT_REPORT_PATH,
    config: StagingAPIConfig | None = None,
) -> Path:
    """Load the artifact and write the staging safety report."""
    settings = config or StagingAPIConfig.from_environment()
    service = PolicyInferenceService(artifact_path, safety_config=settings)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_safety_report(service, settings),
        encoding="utf-8",
    )
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate the staging API safety-control report."""
    options = _parse_args(args)
    report_path = generate_safety_report(options.bundle, options.output)
    print(f"Wrote staging API safety report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
