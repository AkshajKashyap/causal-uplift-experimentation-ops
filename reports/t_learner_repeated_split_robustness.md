# T-Learner Repeated-Split Robustness

## Scope

This report refits the existing logistic T-learner across deterministic, treatment-stratified
train/test splits. No new model family or hyperparameter tuning is introduced.

- Dataset rows: 10,000
- Test fraction per run: 30%
- Seeds: 0, 1, 2, 3, 4

## Per-seed metrics

| Seed | Train rows | Test rows | AUUC | Qini coefficient | Max Qini gain | Top 10% uplift | Top 20% uplift | Top 30% uplift |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 7000 | 3000 | 0.021807 | 0.001474 | 0.005528 | +6.00% | +4.33% | +3.33% |
| 1 | 7000 | 3000 | 0.020168 | 0.001835 | 0.008158 | +3.33% | +5.33% | +3.56% |
| 2 | 7000 | 3000 | 0.022605 | 0.006605 | 0.011264 | +12.67% | +4.67% | +6.22% |
| 3 | 7000 | 3000 | 0.031912 | 0.008245 | 0.016303 | +8.00% | +8.00% | +6.22% |
| 4 | 7000 | 3000 | 0.029440 | 0.007773 | 0.014342 | +14.00% | +10.33% | +7.56% |

## Summary statistics

Population standard deviation is calculated across the requested seed set.

| Metric | Mean | Std | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| AUUC-style area | 0.025186 | 0.004617 | 0.020168 | 0.031912 |
| Qini-style coefficient | 0.005186 | 0.002935 | 0.001474 | 0.008245 |
| Maximum Qini gain | 0.011119 | 0.003932 | 0.005528 | 0.016303 |
| Top 10% estimated uplift | 0.088000 | 0.040089 | 0.033333 | 0.140000 |
| Top 20% estimated uplift | 0.065333 | 0.022959 | 0.043333 | 0.103333 |
| Top 30% estimated uplift | 0.053778 | 0.016534 | 0.033333 | 0.075556 |

- Positive Qini runs: 5 of 5
- Positive Qini rate: 100.0%

## Interpretation

The T-learner appears directionally stable: most repeated splits beat the random-targeting baseline. Qini variability is smaller than its mean, suggesting moderate consistency. This is a finite repeated-split diagnostic, not a confidence interval or proof of out-of-sample policy value.
