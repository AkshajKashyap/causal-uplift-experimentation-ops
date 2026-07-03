"""Generate documentation for the local/staging policy inference API."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from causal_uplift_experimentation_ops.api.schemas import UserFeatures
from causal_uplift_experimentation_ops.api.service import (
    DEFAULT_ARTIFACT_PATH,
    PolicyInferenceService,
)

DEFAULT_REPORT_PATH = Path("reports/api_staging_service.md")
EXAMPLE_USER = UserFeatures(
    user_id=10001,
    age=35,
    prior_purchases=4,
    avg_order_value=82.50,
    days_since_last_purchase=21,
    channel="email",
)


def render_api_report(service: PolicyInferenceService) -> str:
    """Render endpoint, artifact, example, and staging limitation documentation."""
    version = service.version
    response = service.score_user(EXAMPLE_USER)
    request_json = json.dumps(EXAMPLE_USER.model_dump(), indent=2)
    response_json = json.dumps(response.model_dump(), indent=2)
    limitations = "\n".join(
        f"- {limitation}" for limitation in service.config.limitations
    )
    return f"""# FastAPI Staging Policy Service

## Purpose

This local/staging API loads the already-frozen policy artifact and exposes deterministic uplift
scoring. It does not retrain models, write treatment assignments, or authorize production
deployment.

## Artifact loaded

- Bundle: `{service.artifact_path}`
- Artifact version: **{version.artifact_version}**
- Model: **{version.model_name}**
- Policy: **{version.policy_name}**
- Dataset fingerprint: `{version.dataset_fingerprint}`
- Config fingerprint: `{version.config_fingerprint}`
- Package version: **{version.package_version}**

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness and artifact readiness |
| GET | `/version` | Package, artifact, model, policy, and fingerprints |
| GET | `/policy` | Frozen decision rule, features, intended use, and limitations |
| POST | `/score` | Score one user |
| POST | `/score-batch` | Score 1–{service.max_batch_size:,} users |
| GET | `/manifest` | Safe manifest metadata and artifact filenames |

## Example request

```json
{request_json}
```

## Example response

```json
{response_json}
```

The request deliberately excludes `treatment`, `conversion`, `spend`, and `true_uplift`.

## Start locally

```bash
serve-policy-api --host 127.0.0.1 --port 8000
```

Development reload is also supported:

```bash
uvicorn causal_uplift_experimentation_ops.api.app:app --reload
```

## Known limitations

{limitations}

- Request validation covers schema and type constraints, not upstream feature freshness.
- The fitted encoder tolerates unseen non-empty channel labels; their unseen category contributes
  no learned one-hot effect.
- There is no authentication, authorization, rate limiting, durable request log, drift detection,
  service-level objective, or high-availability design.
- Capacity and budget are applied only within each request batch, not across concurrent requests.

## Why this is staging, not production

The service is intentionally local and stateless. Its artifact was trained and evaluated only on
synthetic data, and the pre-registered real-world randomized validation has not occurred.
Production treatment requires security controls, centralized eligibility and budget enforcement,
observability, release approval, rollback automation, and passed prospective guardrails.

## Next steps before production

Run the frozen 1x-traffic, 50%-holdout randomized validation; confirm efficacy, value, ROI,
fairness, and operational guardrails; then design authenticated serving, centralized treatment
allocation, monitoring, and controlled artifact promotion.
"""


def generate_api_report(
    artifact_path: Path | str,
    output_path: Path | str = DEFAULT_REPORT_PATH,
) -> Path:
    """Load the frozen artifact and write staging API documentation."""
    service = PolicyInferenceService(artifact_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_api_report(service), encoding="utf-8")
    return destination


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Generate the staging API Markdown report."""
    options = _parse_args(args)
    report_path = generate_api_report(options.bundle, options.output)
    print(f"Wrote staging API report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
