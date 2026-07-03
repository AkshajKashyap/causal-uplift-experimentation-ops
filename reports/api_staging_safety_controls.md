# Staging API Safety Controls

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

- Authentication required by default: **False**
- API-key environment variable: `CAUSAL_UPLIFT_API_KEY`
- Environment label: `local-staging`

The API key is compared with `secrets.compare_digest` and is never written to the audit log.

## Audit log

- Enabled by default: **False**
- Default path: `artifacts/api_audit_log.jsonl`

Each JSONL event contains:

```text
timestamp, endpoint, request_id, batch_size, artifact_version, model_name,
policy_name, recommended_treatment_count, mean_predicted_uplift,
min_predicted_uplift, max_predicted_uplift, status, error_type, latency_ms
```

Raw user features, API keys, treatment assignments, conversion, spend, and synthetic true uplift
are not logged.

## Budget and capacity behavior

- Guardrail enabled: **True**
- Configured maximum recommendations per run: 1000
- Configured maximum treatment cost per run: 1000.0
- Default treatment cost per user: 1.0

The service first scores every user through the frozen artifact. If configured or request-level
limits bind, it ranks originally recommended users by predicted uplift and keeps the highest
scores. Suppressed users remain in the response with `recommended_treatment=0`.

## Example budget-limited batch response

```json
{
  "request_id": "example-budget-request",
  "batch_size": 3,
  "scores": [
    {
      "request_id": "example-budget-request",
      "user_id": 20001,
      "predicted_uplift": 0.06544670465022923,
      "predicted_control_conversion": 0.18442641753294473,
      "predicted_treatment_conversion": 0.24987312218317395,
      "recommended_treatment": 1,
      "policy_eligible": true,
      "policy_name": "all_positive_uplift",
      "model_name": "logistic_s_learner",
      "artifact_version": "1.0.0",
      "reason": "predicted_uplift > 0",
      "estimated_treatment_cost": 2.0
    },
    {
      "request_id": "example-budget-request",
      "user_id": 20002,
      "predicted_uplift": 0.03605134159276066,
      "predicted_control_conversion": 0.08688846029173496,
      "predicted_treatment_conversion": 0.12293980188449562,
      "recommended_treatment": 0,
      "policy_eligible": true,
      "policy_name": "all_positive_uplift",
      "model_name": "logistic_s_learner",
      "artifact_version": "1.0.0",
      "reason": "predicted_uplift > 0",
      "estimated_treatment_cost": 0.0
    },
    {
      "request_id": "example-budget-request",
      "user_id": 20003,
      "predicted_uplift": 0.019638283599144594,
      "predicted_control_conversion": 0.044349859725270606,
      "predicted_treatment_conversion": 0.0639881433244152,
      "recommended_treatment": 0,
      "policy_eligible": true,
      "policy_name": "all_positive_uplift",
      "model_name": "logistic_s_learner",
      "artifact_version": "1.0.0",
      "reason": "predicted_uplift > 0",
      "estimated_treatment_cost": 0.0
    }
  ],
  "original_recommended_count": 3,
  "final_recommended_count": 1,
  "recommendations_suppressed_by_budget": 2,
  "estimated_treatment_cost": 2.0,
  "guardrail_applied": true
}
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
