# Policy Sensitivity Analysis

## Scope and base assumptions

Cross-fitted model scores are held fixed while economic and operational assumptions vary.

- Dataset rows: 10,000
- Models evaluated: Logistic T-learner, Logistic S-learner, Random-forest T-learner, Random baseline, Synthetic oracle
- Value per conversion: $100.00
- Treatment cost per user: $1.00
- Base budget: None
- Base capacity: None
- Base best learned pair: **Logistic S-learner — All positive uplift**

## One-way sensitivity

| Assumption | Value | Best model | Best policy | Users | Net value | Best ROI | Learned vs random | Learned / oracle | Changed? |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
| Value / conversion | $25.00 | Logistic T-learner | Top 30% | 3,000 | $+2,553.28 | +1.39 | $+2,916.75 | 109.1% | Yes |
| Value / conversion | $50.00 | Logistic S-learner | All positive uplift | 10,000 | $+10,500.00 | +3.79 | $+9,226.94 | 94.8% | No |
| Value / conversion | $100.00 | Logistic S-learner | All positive uplift | 10,000 | $+31,000.00 | +8.58 | $+26,453.88 | 97.4% | No |
| Value / conversion | $150.00 | Logistic S-learner | All positive uplift | 10,000 | $+51,500.00 | +13.37 | $+43,680.82 | 98.0% | No |
| Value / conversion | $200.00 | Logistic S-learner | All positive uplift | 10,000 | $+72,000.00 | +18.16 | $+60,907.76 | 98.2% | No |
| Treatment cost / user | $0.25 | Logistic S-learner | All positive uplift | 10,000 | $+38,500.00 | +37.31 | $+32,453.88 | 98.5% | No |
| Treatment cost / user | $0.50 | Logistic S-learner | All positive uplift | 10,000 | $+36,000.00 | +18.16 | $+30,453.88 | 98.2% | No |
| Treatment cost / user | $1.00 | Logistic S-learner | All positive uplift | 10,000 | $+31,000.00 | +8.58 | $+26,453.88 | 97.4% | No |
| Treatment cost / user | $2.00 | Logistic S-learner | All positive uplift | 10,000 | $+21,000.00 | +3.79 | $+18,453.88 | 94.8% | No |
| Treatment cost / user | $5.00 | Logistic T-learner | Top 30% | 3,000 | $+7,213.13 | +0.92 | $+10,667.01 | 113.4% | Yes |
| Capacity fraction | 5% | Random-forest T-learner | Top 10% | 500 | $+5,634.99 | +11.27 | $+1,882.92 | 110.3% | Yes |
| Capacity fraction | 10% | Logistic S-learner | Top 10% | 1,000 | $+8,578.21 | +8.58 | $+7,181.26 | 96.1% | Yes |
| Capacity fraction | 20% | Logistic T-learner | Top 20% | 2,000 | $+14,445.25 | +8.58 | $+9,899.13 | 101.4% | Yes |
| Capacity fraction | 30% | Logistic T-learner | Top 30% | 3,000 | $+19,213.13 | +8.58 | $+14,667.01 | 104.7% | Yes |
| Capacity fraction | 50% | Logistic T-learner | All positive uplift | 5,000 | $+26,694.15 | +8.58 | $+22,148.03 | 111.8% | Yes |
| Budget | $500.00 | Random-forest T-learner | Top 10% | 500 | $+5,634.99 | +11.27 | $+1,882.92 | 110.3% | Yes |
| Budget | $1,000.00 | Logistic S-learner | Top 10% | 1,000 | $+8,578.21 | +8.58 | $+7,181.26 | 96.1% | Yes |
| Budget | $2,500.00 | Logistic T-learner | Top 30% | 2,500 | $+17,747.94 | +8.58 | $+13,201.82 | 95.7% | Yes |
| Budget | $5,000.00 | Logistic T-learner | All positive uplift | 5,000 | $+26,694.15 | +8.58 | $+22,148.03 | 111.8% | Yes |
| Budget | $10,000.00 | Logistic S-learner | All positive uplift | 10,000 | $+31,000.00 | +8.58 | $+26,453.88 | 97.4% | No |

## Value per conversion × treatment cost

| Scenario | Best model | Best policy | Users | Net value | Best ROI | Learned vs random | Learned / oracle | Changed? |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
| Value / conversion=$25.00 × Treatment cost / user=$0.25 | Logistic S-learner | All positive uplift | 10,000 | $+7,750.00 | +8.58 | $+6,613.47 | 97.4% | No |
| Value / conversion=$25.00 × Treatment cost / user=$0.50 | Logistic S-learner | All positive uplift | 10,000 | $+5,250.00 | +3.79 | $+4,613.47 | 94.8% | No |
| Value / conversion=$25.00 × Treatment cost / user=$1.00 | Logistic T-learner | Top 30% | 3,000 | $+2,553.28 | +1.39 | $+2,916.75 | 109.1% | Yes |
| Value / conversion=$25.00 × Treatment cost / user=$2.00 | Logistic S-learner | Top 10% | 1,000 | $+394.55 | +0.20 | $+2,758.02 | 81.7% | Yes |
| Value / conversion=$25.00 × Treatment cost / user=$5.00 | Logistic S-learner | Top 10% | 1,000 | $-2,605.45 | -0.52 | $+5,758.02 | nan% | Yes |
| Value / conversion=$50.00 × Treatment cost / user=$0.25 | Logistic S-learner | All positive uplift | 10,000 | $+18,000.00 | +18.16 | $+15,226.94 | 98.2% | No |
| Value / conversion=$50.00 × Treatment cost / user=$0.50 | Logistic S-learner | All positive uplift | 10,000 | $+15,500.00 | +8.58 | $+13,226.94 | 97.4% | No |
| Value / conversion=$50.00 × Treatment cost / user=$1.00 | Logistic S-learner | All positive uplift | 10,000 | $+10,500.00 | +3.79 | $+9,226.94 | 94.8% | No |
| Value / conversion=$50.00 × Treatment cost / user=$2.00 | Logistic T-learner | Top 30% | 3,000 | $+5,106.56 | +1.39 | $+5,833.50 | 109.1% | Yes |
| Value / conversion=$50.00 × Treatment cost / user=$5.00 | Logistic S-learner | Top 10% | 1,000 | $-210.89 | -0.04 | $+6,516.05 | nan% | Yes |
| Value / conversion=$100.00 × Treatment cost / user=$0.25 | Logistic S-learner | All positive uplift | 10,000 | $+38,500.00 | +37.31 | $+32,453.88 | 98.5% | No |
| Value / conversion=$100.00 × Treatment cost / user=$0.50 | Logistic S-learner | All positive uplift | 10,000 | $+36,000.00 | +18.16 | $+30,453.88 | 98.2% | No |
| Value / conversion=$100.00 × Treatment cost / user=$1.00 | Logistic S-learner | All positive uplift | 10,000 | $+31,000.00 | +8.58 | $+26,453.88 | 97.4% | No |
| Value / conversion=$100.00 × Treatment cost / user=$2.00 | Logistic S-learner | All positive uplift | 10,000 | $+21,000.00 | +3.79 | $+18,453.88 | 94.8% | No |
| Value / conversion=$100.00 × Treatment cost / user=$5.00 | Logistic T-learner | Top 30% | 3,000 | $+7,213.13 | +0.92 | $+10,667.01 | 113.4% | Yes |
| Value / conversion=$150.00 × Treatment cost / user=$0.25 | Logistic S-learner | All positive uplift | 10,000 | $+59,000.00 | +56.47 | $+49,680.82 | 98.6% | No |
| Value / conversion=$150.00 × Treatment cost / user=$0.50 | Logistic S-learner | All positive uplift | 10,000 | $+56,500.00 | +27.73 | $+47,680.82 | 98.4% | No |
| Value / conversion=$150.00 × Treatment cost / user=$1.00 | Logistic S-learner | All positive uplift | 10,000 | $+51,500.00 | +13.37 | $+43,680.82 | 98.0% | No |
| Value / conversion=$150.00 × Treatment cost / user=$2.00 | Logistic S-learner | All positive uplift | 10,000 | $+41,500.00 | +6.18 | $+35,680.82 | 96.7% | No |
| Value / conversion=$150.00 × Treatment cost / user=$5.00 | Logistic T-learner | Top 30% | 3,000 | $+18,319.69 | +1.87 | $+18,500.51 | 107.5% | Yes |
| Value / conversion=$200.00 × Treatment cost / user=$0.25 | Logistic S-learner | All positive uplift | 10,000 | $+79,500.00 | +75.63 | $+66,907.76 | 98.7% | No |
| Value / conversion=$200.00 × Treatment cost / user=$0.50 | Logistic S-learner | All positive uplift | 10,000 | $+77,000.00 | +37.31 | $+64,907.76 | 98.5% | No |
| Value / conversion=$200.00 × Treatment cost / user=$1.00 | Logistic S-learner | All positive uplift | 10,000 | $+72,000.00 | +18.16 | $+60,907.76 | 98.2% | No |
| Value / conversion=$200.00 × Treatment cost / user=$2.00 | Logistic S-learner | All positive uplift | 10,000 | $+62,000.00 | +8.58 | $+52,907.76 | 97.4% | No |
| Value / conversion=$200.00 × Treatment cost / user=$5.00 | Logistic T-learner | All positive uplift | 9,029 | $+32,211.94 | +2.83 | $+29,119.70 | 92.9% | Yes |

## Capacity × treatment cost

| Scenario | Best model | Best policy | Users | Net value | Best ROI | Learned vs random | Learned / oracle | Changed? |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
| Capacity fraction=5% × Treatment cost / user=$0.25 | Random-forest T-learner | Top 10% | 500 | $+6,009.99 | +48.08 | $+1,882.92 | 109.6% | Yes |
| Capacity fraction=5% × Treatment cost / user=$0.50 | Random-forest T-learner | Top 10% | 500 | $+5,884.99 | +23.54 | $+1,882.92 | 109.8% | Yes |
| Capacity fraction=5% × Treatment cost / user=$1.00 | Random-forest T-learner | Top 10% | 500 | $+5,634.99 | +11.27 | $+1,882.92 | 110.3% | Yes |
| Capacity fraction=5% × Treatment cost / user=$2.00 | Random-forest T-learner | Top 10% | 500 | $+5,134.99 | +5.13 | $+1,882.92 | 111.4% | Yes |
| Capacity fraction=5% × Treatment cost / user=$5.00 | Random-forest T-learner | Top 10% | 500 | $+3,634.99 | +1.45 | $+1,882.92 | 116.9% | Yes |
| Capacity fraction=10% × Treatment cost / user=$0.25 | Logistic S-learner | Top 10% | 1,000 | $+9,328.21 | +37.31 | $+7,181.26 | 96.4% | Yes |
| Capacity fraction=10% × Treatment cost / user=$0.50 | Logistic S-learner | Top 10% | 1,000 | $+9,078.21 | +18.16 | $+7,181.26 | 96.3% | Yes |
| Capacity fraction=10% × Treatment cost / user=$1.00 | Logistic S-learner | Top 10% | 1,000 | $+8,578.21 | +8.58 | $+7,181.26 | 96.1% | Yes |
| Capacity fraction=10% × Treatment cost / user=$2.00 | Logistic S-learner | Top 10% | 1,000 | $+7,578.21 | +3.79 | $+7,181.26 | 95.6% | Yes |
| Capacity fraction=10% × Treatment cost / user=$5.00 | Logistic S-learner | Top 10% | 1,000 | $+4,578.21 | +0.92 | $+7,181.26 | 92.8% | Yes |
| Capacity fraction=20% × Treatment cost / user=$0.25 | Logistic T-learner | Top 20% | 2,000 | $+15,945.25 | +37.31 | $+9,899.13 | 101.3% | Yes |
| Capacity fraction=20% × Treatment cost / user=$0.50 | Logistic T-learner | Top 20% | 2,000 | $+15,445.25 | +18.16 | $+9,899.13 | 101.4% | Yes |
| Capacity fraction=20% × Treatment cost / user=$1.00 | Logistic T-learner | Top 20% | 2,000 | $+14,445.25 | +8.58 | $+9,899.13 | 101.4% | Yes |
| Capacity fraction=20% × Treatment cost / user=$2.00 | Logistic T-learner | Top 20% | 2,000 | $+12,445.25 | +3.79 | $+9,899.13 | 101.7% | Yes |
| Capacity fraction=20% × Treatment cost / user=$5.00 | Logistic T-learner | Top 20% | 2,000 | $+6,445.25 | +0.92 | $+9,899.13 | 103.3% | Yes |
| Capacity fraction=30% × Treatment cost / user=$0.25 | Logistic T-learner | Top 30% | 3,000 | $+21,463.13 | +37.31 | $+15,417.01 | 104.1% | Yes |
| Capacity fraction=30% × Treatment cost / user=$0.50 | Logistic T-learner | Top 30% | 3,000 | $+20,713.13 | +18.16 | $+15,167.01 | 104.3% | Yes |
| Capacity fraction=30% × Treatment cost / user=$1.00 | Logistic T-learner | Top 30% | 3,000 | $+19,213.13 | +8.58 | $+14,667.01 | 104.7% | Yes |
| Capacity fraction=30% × Treatment cost / user=$2.00 | Logistic T-learner | Top 30% | 3,000 | $+16,213.13 | +3.79 | $+13,667.01 | 105.6% | Yes |
| Capacity fraction=30% × Treatment cost / user=$5.00 | Logistic T-learner | Top 30% | 3,000 | $+7,213.13 | +0.92 | $+10,667.01 | 113.4% | Yes |
| Capacity fraction=50% × Treatment cost / user=$0.25 | Logistic T-learner | All positive uplift | 5,000 | $+30,444.15 | +37.31 | $+24,398.03 | 110.2% | Yes |
| Capacity fraction=50% × Treatment cost / user=$0.50 | Logistic T-learner | All positive uplift | 5,000 | $+29,194.15 | +18.16 | $+23,648.03 | 110.7% | Yes |
| Capacity fraction=50% × Treatment cost / user=$1.00 | Logistic T-learner | All positive uplift | 5,000 | $+26,694.15 | +8.58 | $+22,148.03 | 111.8% | Yes |
| Capacity fraction=50% × Treatment cost / user=$2.00 | Logistic T-learner | All positive uplift | 5,000 | $+21,694.15 | +3.79 | $+19,148.03 | 115.0% | Yes |
| Capacity fraction=50% × Treatment cost / user=$5.00 | Logistic T-learner | Top 30% | 3,000 | $+7,213.13 | +0.92 | $+10,667.01 | 113.4% | Yes |

## Decision stability

| Measure | Value |
| --- | ---: |
| Scenarios | 70 |
| Most frequent best model | Logistic S-learner |
| Most frequent best policy | All positive uplift |
| Most stable pair | Logistic S-learner / All positive uplift |
| Same-model win rate | 51.4% |
| Same-policy win rate | 47.1% |
| Learned beats random rate | 100.0% |
| Positive learned net-value rate | 97.1% |
| Average learned / oracle ratio | 102.1% |
| Worst-case learned net value | $-2,605.45 |
| Worst-case best ROI | -0.52 |
| Best-case learned net value | $+79,500.00 |
| Best-case ROI | +75.63 |

## Break-even analysis

- Base best model-policy: **Logistic S-learner — All positive uplift**
- Maximum treatment cost with positive net value: **$4.10 per user**
- Minimum value per conversion with positive net value: **$24.39**

| Policy | Users | Incremental conversions | Break-even cost / user | Profitable at base cost? |
| --- | ---: | ---: | ---: | :---: |
| Top 10% | 1,000 | +95.78 | $9.58 | Yes |
| Top 20% | 2,000 | +152.14 | $7.61 | Yes |
| Top 30% | 3,000 | +203.25 | $6.77 | Yes |
| All positive uplift | 10,000 | +410.00 | $4.10 | Yes |

## Interpretation

The recommendation is fragile across the tested scenarios. Value / conversion creates the largest one-way swing in best learned net value. The base policy breaks even near a treatment cost of $4.10 per user, so sufficiently high costs can erase apparent value. Target-all outcomes largely reproduce the overall A/B effect and are not evidence of superior ranking; constrained depths are more informative about who should be treated. Oracle comparisons use unavailable synthetic truth, and every result remains an offline simulation rather than production proof.
