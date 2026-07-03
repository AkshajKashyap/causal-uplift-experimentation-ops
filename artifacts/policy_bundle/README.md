# Frozen Policy Bundle

This directory contains artifact version `1.0.0` for
`logistic_s_learner` with policy `all_positive_uplift`.

Files:

- `model.joblib`: fitted Logistic S-learner and frozen decision configuration
- `policy_config.json`: policy, evidence, economics, use, and limitation contract
- `manifest.json`: data, feature, config, package, and artifact-file fingerprints
- `feature_columns.json`: ordered required input features
- `value_assumptions.json`: conversion value, treatment cost, capacity, and budget
- `batch_scores.csv`: generated smoke-test scores; excluded from source control

Reproduce from the repository root:

```bash
generate-synthetic-experiment
generate-policy-artifact
```

Score another compatible CSV:

```bash
score-policy-batch --bundle artifacts/policy_bundle --input path/to/input.csv
```

This bundle is validated only on synthetic data. It must not trigger production treatment until
the pre-registered real-world randomized validation passes.
