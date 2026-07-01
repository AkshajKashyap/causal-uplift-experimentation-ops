# Synthetic Logistic T-Learner Report

## Scope

This baseline fits separate logistic conversion models to treated and control training rows.
Predicted uplift is the treated conversion probability minus the control conversion probability.
All metrics below use only the held-out test rows.

## Leakage-safe split

| Split | Rows | Control | Treatment |
| --- | ---: | ---: | ---: |
| Train | 7,000 | 3,500 | 3,500 |
| Test | 3,000 | 1,500 | 1,500 |

Feature columns: `age`, `prior_purchases`, `avg_order_value`, `days_since_last_purchase`, `channel`

Excluded from features: treatment, conversion, spend, user identifier, and synthetic true uplift.

## Test-set uplift ranking

Bin 1 contains the highest predicted uplift.

| Bin | Rows | Mean predicted uplift | Treated conversion | Control conversion | Observed uplift |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 300 | +0.1231 | 27.74% | 21.38% | +6.36% |
| 2 | 300 | +0.0870 | 21.32% | 13.41% | +7.91% |
| 3 | 300 | +0.0687 | 17.78% | 12.73% | +5.05% |
| 4 | 300 | +0.0567 | 16.13% | 12.41% | +3.72% |
| 5 | 300 | +0.0464 | 17.12% | 11.04% | +6.08% |
| 6 | 300 | +0.0377 | 8.86% | 9.15% | -0.29% |
| 7 | 300 | +0.0294 | 10.56% | 12.95% | -2.39% |
| 8 | 300 | +0.0203 | 6.85% | 5.84% | +1.01% |
| 9 | 300 | +0.0106 | 7.36% | 6.57% | +0.79% |
| 10 | 300 | -0.0008 | 9.66% | 8.39% | +1.27% |

## Curve metrics

| Metric | T-learner | Synthetic oracle |
| --- | ---: | ---: |
| AUUC-style area | 0.019076 | 0.015474 |
| Qini-style coefficient | 0.005076 | 0.001474 |

- Maximum T-learner Qini gain: 0.013716 at 48.6% targeted
- Random-targeting assessment: The positive Qini-style coefficient indicates better ranking than random targeting.

## Top-k targeting

| Targeted | Users | Treated | Control | Estimated uplift | Incremental conversions |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10% | 300 | 155 | 145 | +8.00% | +24.00 |
| 20% | 600 | 291 | 309 | +6.33% | +38.00 |
| 30% | 900 | 426 | 474 | +4.89% | +44.00 |

## Interpretation

This is a first linear-logit ranking baseline built from two logistic outcome models.
The positive Qini-style coefficient indicates better ranking than random targeting.

The oracle comparison is available only because this is synthetic data. Finite-sample metrics use
noisy observed binary outcomes, so the oracle ordering is not guaranteed to maximize every
realized test-set curve. The T-learner does not quantify uncertainty, tune hyperparameters, or
capture arbitrary nonlinear treatment-effect patterns, so results should be treated as a
benchmark rather than a production targeting policy.
