# Synthetic Oracle Uplift Evaluation

## Scope

This is an evaluation-protocol check using the synthetic dataset's known `true_uplift` as an
oracle score. It is not a trained model and its metrics must not be interpreted as real model
performance.

## Leakage-safe split

| Split | Rows | Control | Treatment |
| --- | ---: | ---: | ---: |
| Train | 7,000 | 3,500 | 3,500 |
| Test | 3,000 | 1,500 | 1,500 |

Feature columns: `age`, `prior_purchases`, `avg_order_value`, `days_since_last_purchase`, `channel`

Excluded from features: treatment, conversion, spend, user identifier, and synthetic true uplift.

## Test-set uplift ranking

Bin 1 contains the highest oracle uplift scores.

| Bin | Rows | Mean oracle score | Treated conversion | Control conversion | Observed uplift |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 300 | 0.1136 | 26.85% | 22.52% | +4.33% |
| 2 | 300 | 0.0780 | 21.13% | 20.25% | +0.87% |
| 3 | 300 | 0.0630 | 18.62% | 13.55% | +5.07% |
| 4 | 300 | 0.0526 | 15.07% | 10.39% | +4.68% |
| 5 | 300 | 0.0422 | 16.23% | 13.70% | +2.54% |
| 6 | 300 | 0.0338 | 13.46% | 6.94% | +6.52% |
| 7 | 300 | 0.0273 | 9.40% | 7.95% | +1.45% |
| 8 | 300 | 0.0217 | 8.97% | 5.81% | +3.16% |
| 9 | 300 | 0.0156 | 6.29% | 9.22% | -2.93% |
| 10 | 300 | 0.0033 | 7.10% | 2.76% | +4.34% |

## Curve metrics

- AUUC-style area: 0.015474
- Qini-style coefficient: 0.001474
- Maximum Qini gain: 0.007013 at 60.7% targeted

The cumulative uplift curve uses inverse-propensity contributions. The Qini-style curve subtracts
the straight-line random-targeting baseline; both areas use trapezoidal integration.

## Top-k targeting

| Targeted | Users | Treated | Control | Estimated uplift | Incremental conversions |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10% | 300 | 149 | 151 | +4.00% | +12.00 |
| 20% | 600 | 291 | 309 | +1.33% | +8.00 |
| 30% | 900 | 436 | 464 | +2.22% | +20.00 |

## Interpretation

The oracle score ranks users by the known treatment effect used to generate this synthetic data.
These results validate the split, ranking, curve, and policy calculations under controlled ground
truth. They establish an evaluation baseline only; no uplift model has been trained or evaluated.
