# FastAPI Staging Policy Service

## Purpose

This local/staging API loads the already-frozen policy artifact and exposes deterministic uplift
scoring. It does not retrain models, write treatment assignments, or authorize production
deployment.

## Artifact loaded

- Bundle: `artifacts/policy_bundle`
- Artifact version: **1.0.0**
- Model: **logistic_s_learner**
- Policy: **all_positive_uplift**
- Dataset fingerprint: `543bdc505f595f138f9e4fe487723f4958cf0ec888c3d9321435c1ce52ad0a57`
- Config fingerprint: `38cee44e01f2f092ba0eb179348fe3980381fc81fe49c45baf32d41121db5725`
- Package version: **0.1.0**

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness and artifact readiness |
| GET | `/version` | Package, artifact, model, policy, and fingerprints |
| GET | `/policy` | Frozen decision rule, features, intended use, and limitations |
| POST | `/score` | Score one user |
| POST | `/score-batch` | Score 1–1,000 users |
| GET | `/manifest` | Safe manifest metadata and artifact filenames |
| GET | `/metrics` | Process-local operational counters and mean latency |

## Example request

```json
{
  "user_id": 10001,
  "age": 35,
  "prior_purchases": 4,
  "avg_order_value": 82.5,
  "days_since_last_purchase": 21,
  "channel": "email"
}
```

## Example response

```json
{
  "request_id": "example-request-id",
  "user_id": 10001,
  "predicted_uplift": 0.06544670465022923,
  "predicted_control_conversion": 0.18442641753294473,
  "predicted_treatment_conversion": 0.24987312218317395,
  "recommended_treatment": 1,
  "policy_eligible": true,
  "policy_name": "all_positive_uplift",
  "model_name": "logistic_s_learner",
  "artifact_version": "1.0.0",
  "reason": "predicted_uplift > 0",
  "estimated_treatment_cost": 1.0
}
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

- The policy has been trained and evaluated only on synthetic data.
- Prospective real-world randomized validation is required before deployment.
- All-positive wins without budget or capacity constraints largely because broad treatment is profitable under the configured economics.
- Ranking quality matters more when treatment capacity or budget is constrained.
- Economic conclusions may change with treatment cost or conversion value.

- Request validation covers schema and type constraints, not upstream feature freshness.
- The fitted encoder tolerates unseen non-empty channel labels; their unseen category contributes
  no learned one-hot effect.
- Optional staging API-key authentication and local JSONL audit logging are not substitutes for
  enterprise identity, centralized logs, or authorization.
- There is no rate limiting, drift detection, service-level objective, or high-availability
  design.
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
