# Cross-Fitted Uplift Model Comparison

## Scope

Every fitted model receives one out-of-fold prediction per row from deterministic,
treatment-stratified 5-fold cross-fitting. Bootstrap intervals resample the resulting
out-of-fold scored rows within treatment arms.

- Dataset rows: 10,000
- Cross-fitting folds: 5
- Bootstrap samples per model: 100
- Models compared: Logistic T-learner, Logistic S-learner, Random-forest T-learner, Random baseline, Synthetic oracle
- Leakage-safe features: `age`, `prior_purchases`, `avg_order_value`, `days_since_last_purchase`, `channel`

## Model comparison

| Qini rank | Model | AUUC | Qini | Max Qini gain | Top 10% | Top 20% | Top 30% | Qini vs random |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Synthetic oracle | 0.026417 | 0.005917 | 0.011300 | +11.20% | +7.90% | +7.07% | +0.002795 |
| 2 | Logistic T-learner | 0.026075 | 0.005575 | 0.010768 | +9.20% | +7.40% | +6.40% | +0.002454 |
| 3 | Logistic S-learner | 0.024609 | 0.004109 | 0.008846 | +9.20% | +6.00% | +5.33% | +0.000987 |
| 4 | Random baseline | 0.023621 | 0.003121 | 0.007414 | +3.20% | +4.50% | +4.40% | +0.000000 |
| 5 | Random-forest T-learner | 0.020687 | 0.000187 | 0.007045 | +9.00% | +5.80% | +5.20% | -0.002934 |

Best fitted model by Qini coefficient: **Logistic T-learner**

## Bootstrap Qini uncertainty

| Model | Mean | 2.5% | 50% | 97.5% | Positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic T-learner | 0.005750 | 0.001672 | 0.005579 | 0.010102 | 100.0% |
| Logistic S-learner | 0.003987 | 0.000148 | 0.004071 | 0.007591 | 98.0% |
| Random-forest T-learner | -0.000034 | -0.004368 | 0.000384 | 0.004717 | 55.0% |
| Random baseline | 0.002870 | -0.000177 | 0.002661 | 0.006886 | 95.0% |
| Synthetic oracle | 0.005960 | 0.002046 | 0.005761 | 0.010463 | 100.0% |

## Interpretation

Logistic T-learner has the strongest fitted-model Qini coefficient and beats the realized random-score baseline. Its bootstrap Qini interval excludes zero. Its realized Qini difference from the synthetic oracle is -0.000342; finite-sample outcome noise means the oracle need not maximize every observed curve. The oracle exists only because synthetic true uplift is known. These randomized synthetic results validate the comparison framework, but do not prove causal lift in another real-world population.
