# Targeting Policy Simulation

## Scope and assumptions

Cross-fitted predictions are converted into offline targeting decisions. Incremental conversions
use the randomized treatment-minus-control conversion difference within selected users.

- Dataset rows: 10,000
- Cross-fitting folds: 5
- Value per conversion: $100.00
- Treatment cost per user: $1.00
- Budget: None
- Capacity fraction: None
- Minimum predicted uplift: None
- Models evaluated: Logistic T-learner, Logistic S-learner, Random-forest T-learner, Random baseline, Synthetic oracle
- Policies evaluated: Top 10%, Top 20%, Top 30%, All positive uplift, Random matched to 20%, Oracle matched to 20%

## Model-policy comparison

| Model | Policy | Users | Fraction | Mean predicted uplift | Observed uplift | Incremental conversions | Gross value | Cost | Net value | ROI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic T-learner | Top 10% | 1,000 | 10.0% | +10.91% | +8.55% | +85.49 | $+8,549.39 | $1,000.00 | $+7,549.39 | +7.55 |
| Logistic T-learner | Top 20% | 2,000 | 20.0% | +9.33% | +8.22% | +164.45 | $+16,445.25 | $2,000.00 | $+14,445.25 | +7.22 |
| Logistic T-learner | Top 30% | 3,000 | 30.0% | +8.32% | +7.40% | +222.13 | $+22,213.13 | $3,000.00 | $+19,213.13 | +6.40 |
| Logistic T-learner | All positive uplift | 9,029 | 90.3% | +4.78% | +4.28% | +386.78 | $+38,678.47 | $9,029.00 | $+29,649.47 | +3.28 |
| Logistic T-learner | Random matched to 20% | 2,000 | 20.0% | +4.21% | +3.27% | +65.46 | $+6,546.12 | $2,000.00 | $+4,546.12 | +2.27 |
| Logistic T-learner | Oracle matched to 20% | 2,000 | 20.0% | +7.72% | +8.12% | +162.39 | $+16,239.41 | $2,000.00 | $+14,239.41 | +7.12 |
| Logistic S-learner | Top 10% | 1,000 | 10.0% | +7.21% | +9.58% | +95.78 | $+9,578.21 | $1,000.00 | $+8,578.21 | +8.58 |
| Logistic S-learner | Top 20% | 2,000 | 20.0% | +6.55% | +7.61% | +152.14 | $+15,213.97 | $2,000.00 | $+13,213.97 | +6.61 |
| Logistic S-learner | Top 30% | 3,000 | 30.0% | +6.11% | +6.77% | +203.25 | $+20,324.66 | $3,000.00 | $+17,324.66 | +5.77 |
| Logistic S-learner | All positive uplift | 10,000 | 100.0% | +4.23% | +4.10% | +410.00 | $+41,000.00 | $10,000.00 | $+31,000.00 | +3.10 |
| Logistic S-learner | Random matched to 20% | 2,000 | 20.0% | +4.22% | +3.27% | +65.46 | $+6,546.12 | $2,000.00 | $+4,546.12 | +2.27 |
| Logistic S-learner | Oracle matched to 20% | 2,000 | 20.0% | +6.28% | +8.12% | +162.39 | $+16,239.41 | $2,000.00 | $+14,239.41 | +7.12 |
| Random-forest T-learner | Top 10% | 1,000 | 10.0% | +17.25% | +8.19% | +81.90 | $+8,189.96 | $1,000.00 | $+7,189.96 | +7.19 |
| Random-forest T-learner | Top 20% | 2,000 | 20.0% | +14.11% | +5.70% | +114.02 | $+11,402.10 | $2,000.00 | $+9,402.10 | +4.70 |
| Random-forest T-learner | Top 30% | 3,000 | 30.0% | +12.12% | +5.37% | +160.98 | $+16,097.52 | $3,000.00 | $+13,097.52 | +4.37 |
| Random-forest T-learner | All positive uplift | 7,278 | 72.8% | +6.93% | +3.87% | +281.70 | $+28,169.80 | $7,278.00 | $+20,891.80 | +2.87 |
| Random-forest T-learner | Random matched to 20% | 2,000 | 20.0% | +4.17% | +3.27% | +65.46 | $+6,546.12 | $2,000.00 | $+4,546.12 | +2.27 |
| Random-forest T-learner | Oracle matched to 20% | 2,000 | 20.0% | +7.83% | +8.12% | +162.39 | $+16,239.41 | $2,000.00 | $+14,239.41 | +7.12 |
| Random baseline | Top 10% | 1,000 | 10.0% | +94.99% | +3.25% | +32.52 | $+3,252.01 | $1,000.00 | $+2,252.01 | +2.25 |
| Random baseline | Top 20% | 2,000 | 20.0% | +89.83% | +4.68% | +93.63 | $+9,363.06 | $2,000.00 | $+7,363.06 | +3.68 |
| Random baseline | Top 30% | 3,000 | 30.0% | +84.72% | +4.57% | +137.13 | $+13,712.61 | $3,000.00 | $+10,712.61 | +3.57 |
| Random baseline | All positive uplift | 10,000 | 100.0% | +49.71% | +4.10% | +410.00 | $+41,000.00 | $10,000.00 | $+31,000.00 | +3.10 |
| Random baseline | Random matched to 20% | 2,000 | 20.0% | +49.98% | +3.27% | +65.46 | $+6,546.12 | $2,000.00 | $+4,546.12 | +2.27 |
| Random baseline | Oracle matched to 20% | 2,000 | 20.0% | +49.56% | +8.12% | +162.39 | $+16,239.41 | $2,000.00 | $+14,239.41 | +7.12 |
| Synthetic oracle | Top 10% | 1,000 | 10.0% | +11.21% | +9.93% | +99.31 | $+9,930.99 | $1,000.00 | $+8,930.99 | +8.93 |
| Synthetic oracle | Top 20% | 2,000 | 20.0% | +9.48% | +8.12% | +162.39 | $+16,239.41 | $2,000.00 | $+14,239.41 | +7.12 |
| Synthetic oracle | Top 30% | 3,000 | 30.0% | +8.44% | +7.12% | +213.58 | $+21,358.44 | $3,000.00 | $+18,358.44 | +6.12 |
| Synthetic oracle | All positive uplift | 9,660 | 96.6% | +4.69% | +4.29% | +414.82 | $+41,481.80 | $9,660.00 | $+31,821.80 | +3.29 |
| Synthetic oracle | Random matched to 20% | 2,000 | 20.0% | +4.50% | +3.27% | +65.46 | $+6,546.12 | $2,000.00 | $+4,546.12 | +2.27 |
| Synthetic oracle | Oracle matched to 20% | 2,000 | 20.0% | +9.48% | +8.12% | +162.39 | $+16,239.41 | $2,000.00 | $+14,239.41 | +7.12 |

## Best policy by model

| Model | Best net-value policy | Net value | ROI |
| --- | --- | ---: | ---: |
| Synthetic oracle | All positive uplift | $+31,821.80 | +3.29 |
| Logistic S-learner | All positive uplift | $+31,000.00 | +3.10 |
| Random baseline | All positive uplift | $+31,000.00 | +3.10 |
| Logistic T-learner | All positive uplift | $+29,649.47 | +3.28 |
| Random-forest T-learner | All positive uplift | $+20,891.80 | +2.87 |

- Best learned pair by net value: **Logistic S-learner — All positive uplift** ($+31,000.00)
- Best learned pair by ROI: **Logistic S-learner — Top 10%** (+8.58)

## Interpretation

Logistic S-learner with All positive uplift has the highest learned-policy net value. The best learned net value differs from the random-score benchmark by $+0.00 and from the synthetic oracle by $-821.80. For the best-net model, targeting 30% reduces ROI versus the better shallower depth. Treatment cost makes deeper targeting less attractive when marginal incremental conversion falls; uplift ranking matters only when it produces enough incremental value to cover that cost. The oracle is synthetic-only, and this remains an offline randomized-data simulation—not proof of production impact.
