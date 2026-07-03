# Staging Observability Report

## Scope and identity

- Artifact version: **1.0.0**
- Model: **logistic_s_learner**
- Policy: **all_positive_uplift**
- Dataset fingerprint: `543bdc505f595f138f9e4fe487723f4958cf0ec888c3d9321435c1ce52ad0a57`
- Current raw-input source: `reference rows joined to batch scores by user_id`

This report provides deterministic offline/staging monitoring. It is not continuous production
observability and does not grant production approval.

## Input drift

- Status: **pass**

| feature | feature_type | metric_name | reference_value | current_value | absolute_difference | severity | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| age | numeric | missing_rate | 0.000000 | 0.000000 | 0.000000 | pass | Absolute missing-rate change; warn >=2%, fail >=10%. |
| age | numeric | mean | 48.772700 | 48.772700 | 0.000000 | pass | Standardized mean shift=0.0000; warn >=0.10, fail >=0.25. |
| age | numeric | standard_deviation_ratio | 1.000000 | 1.000000 | 0.000000 | pass | Ratio current/reference; warn shift >=0.20, fail >=0.50. |
| age | numeric | population_stability_index | 0.000000 | 0.000000 | 0.000000 | pass | PSI warn >=0.10, fail >=0.25. |
| prior_purchases | numeric | missing_rate | 0.000000 | 0.000000 | 0.000000 | pass | Absolute missing-rate change; warn >=2%, fail >=10%. |
| prior_purchases | numeric | mean | 3.013400 | 3.013400 | 0.000000 | pass | Standardized mean shift=0.0000; warn >=0.10, fail >=0.25. |
| prior_purchases | numeric | standard_deviation_ratio | 1.000000 | 1.000000 | 0.000000 | pass | Ratio current/reference; warn shift >=0.20, fail >=0.50. |
| prior_purchases | numeric | population_stability_index | 0.000000 | 0.000000 | 0.000000 | pass | PSI warn >=0.10, fail >=0.25. |
| avg_order_value | numeric | missing_rate | 0.000000 | 0.000000 | 0.000000 | pass | Absolute missing-rate change; warn >=2%, fail >=10%. |
| avg_order_value | numeric | mean | 80.724847 | 80.724847 | 0.000000 | pass | Standardized mean shift=0.0000; warn >=0.10, fail >=0.25. |
| avg_order_value | numeric | standard_deviation_ratio | 1.000000 | 1.000000 | 0.000000 | pass | Ratio current/reference; warn shift >=0.20, fail >=0.50. |
| avg_order_value | numeric | population_stability_index | 0.000000 | 0.000000 | 0.000000 | pass | PSI warn >=0.10, fail >=0.25. |
| days_since_last_purchase | numeric | missing_rate | 0.000000 | 0.000000 | 0.000000 | pass | Absolute missing-rate change; warn >=2%, fail >=10%. |
| days_since_last_purchase | numeric | mean | 69.291900 | 69.291900 | 0.000000 | pass | Standardized mean shift=0.0000; warn >=0.10, fail >=0.25. |
| days_since_last_purchase | numeric | standard_deviation_ratio | 1.000000 | 1.000000 | 0.000000 | pass | Ratio current/reference; warn shift >=0.20, fail >=0.50. |
| days_since_last_purchase | numeric | population_stability_index | 0.000000 | 0.000000 | 0.000000 | pass | PSI warn >=0.10, fail >=0.25. |
| channel | categorical | missing_rate | 0.000000 | 0.000000 | 0.000000 | pass | Absolute missing-rate change; warn >=2%, fail >=10%. |
| channel | categorical | unseen_category_rate | 0.000000 | 0.000000 | 0.000000 | pass | Current values absent from reference; warn >=1%, fail >=5%. |
| channel | categorical | category_frequency:email | 0.296000 | 0.296000 | 0.000000 | pass | Absolute category-frequency change. |
| channel | categorical | category_frequency:organic | 0.254500 | 0.254500 | 0.000000 | pass | Absolute category-frequency change. |
| channel | categorical | category_frequency:paid_search | 0.252400 | 0.252400 | 0.000000 | pass | Absolute category-frequency change. |
| channel | categorical | category_frequency:social | 0.197100 | 0.197100 | 0.000000 | pass | Absolute category-frequency change. |
| channel | categorical | population_stability_index | 0.000000 | 0.000000 | 0.000000 | pass | PSI warn >=0.10, fail >=0.25. |

## Prediction drift

- Status: **warn**

| metric_name | reference_value | current_value | absolute_difference | severity | notes |
| --- | --- | --- | --- | --- | --- |
| predicted_uplift_mean | 0.042299 | 0.042299 | 0.000000 | pass | Distribution summary; mean shift warn >=0.01, fail >=0.03. |
| predicted_uplift_std | 0.015062 | 0.015062 | 0.000000 | pass | Distribution summary; mean shift warn >=0.01, fail >=0.03. |
| predicted_uplift_min | 0.004798 | 0.004798 | 0.000000 | pass | Distribution summary; mean shift warn >=0.01, fail >=0.03. |
| predicted_uplift_max | 0.096410 | 0.096410 | 0.000000 | pass | Distribution summary; mean shift warn >=0.01, fail >=0.03. |
| predicted_uplift_p01 | 0.012410 | 0.012410 | 0.000000 | pass |  |
| predicted_uplift_p05 | 0.019751 | 0.019751 | 0.000000 | pass |  |
| predicted_uplift_p25 | 0.031593 | 0.031593 | 0.000000 | pass |  |
| predicted_uplift_p50 | 0.040912 | 0.040912 | 0.000000 | pass |  |
| predicted_uplift_p75 | 0.052039 | 0.052039 | 0.000000 | pass |  |
| predicted_uplift_p95 | 0.069501 | 0.069501 | 0.000000 | pass |  |
| predicted_uplift_p99 | 0.081174 | 0.081174 | 0.000000 | pass |  |
| recommendation_rate | 1.000000 | 1.000000 | 0.000000 | warn | Shift warn >=5%, fail >=15%; extreme stable rates are still warned. |
| policy_eligibility_rate | 1.000000 | 1.000000 | 0.000000 | pass |  |
| negative_score_rate | 0.000000 | 0.000000 | 0.000000 | pass | Shift warn >=10%, fail >=25%; rates above 99% are warned. |
| positive_score_rate | 1.000000 | 1.000000 | 0.000000 | warn | Shift warn >=10%, fail >=25%; rates above 99% are warned. |
| estimated_treatment_cost | 10000.000000 | 10000.000000 | 0.000000 | pass |  |

## API audit log

- Status: **pass**

| metric | value |
| --- | --- |
| total_events | 6 |
| total_score_requests | 3 |
| total_batch_requests | 3 |
| total_users_scored | 15 |
| total_recommendations | 12 |
| total_errors | 0 |
| error_rate | 0.000000 |
| mean_latency_ms | 19.750000 |
| p50_latency_ms | 18.650000 |
| p95_latency_ms | 30.525000 |
| max_latency_ms | 31.400000 |
| artifact_versions_seen | 1.0.0 |
| model_names_seen | logistic_s_learner |
| policy_names_seen | all_positive_uplift |

### Endpoint activity

| endpoint | requests | recommendations |
| --- | --- | --- |
| /score | 3 | 3 |
| /score-batch | 3 | 9 |

## Operational health

- Overall status: **warn**
- Pass checks: 8
- Warning checks: 2
- Failed checks: 0

| check | status | details | blocking |
| --- | --- | --- | --- |
| input_drift | pass | 23 input drift metrics evaluated. | False |
| prediction_drift | warn | Non-pass metrics: recommendation_rate, positive_score_rate | False |
| audit_log | pass | 6 audit events analyzed. | False |
| artifact_manifest | pass | Artifact manifest loaded from artifacts/policy_bundle/manifest.json. | False |
| artifact_version_consistency | pass | Observed artifact versions are consistent with 1.0.0. | False |
| policy_card | pass | Found required evidence: reports/policy_card.md | False |
| experiment_preregistration | pass | Found required evidence: reports/experiment_preregistration.md | False |
| prospective_trial_report | pass | Found required evidence: reports/prospective_policy_trial.md | False |
| prospective_trial_guardrails | pass | Final simulated prospective-trial guardrails are marked PASS. | False |
| synthetic_validation_scope | warn | All model, policy, and prospective evidence remains synthetic-only. | False |

## Promotion gate

- Decision: **hold**
- Recommended next action: Keep the artifact in offline/staging use and resolve the listed evidence or health gaps before another promotion review.

Reasons:

- Evidence is synthetic-only; a real pre-registered randomized trial is required before production promotion.

### Blocking issues

- Evidence is synthetic-only; a real pre-registered randomized trial is required before production promotion.

### Non-blocking warnings

- Non-pass metrics: recommendation_rate, positive_score_rate
- All model, policy, and prospective evidence remains synthetic-only.

## Limitation

These checks inspect local CSV/JSONL snapshots and static reports. They do not provide durable
telemetry, alerting, tracing, data freshness enforcement, or a production SLO. All evaluation
evidence remains synthetic, so a real pre-registered randomized trial is still required before
production treatment delivery.
