# Policy Artifact Manifest

## Frozen artifact

- Artifact directory: `artifacts/policy_bundle`
- Artifact version: **1.0.0**
- Package version: **0.1.0**
- Created: 2026-07-05T02:05:36+00:00
- Data rows: 10,000
- Data columns: 10
- Dataset fingerprint: `543bdc505f595f138f9e4fe487723f4958cf0ec888c3d9321435c1ce52ad0a57`
- Dataset content SHA-256: `6688baab7941f6867a1eaa0c9c367f4aeedcad2f4879061ea8ca114f8c38dba5`
- Feature contract fingerprint: `38d7db792cc1401fe9e26b28cf1e7a60627ab19f44e8c517d92668b5fc132fc7`
- Policy config fingerprint: `38cee44e01f2f092ba0eb179348fe3980381fc81fe49c45baf32d41121db5725`

## Artifact files

| File | SHA-256 |
| --- | --- |
| `artifacts/policy_bundle/README.md` | `ec7e4fe43a16f742d830f45e75838728be82936e538a9c0aae2fb1e8cbd3c284` |
| `artifacts/policy_bundle/batch_scores.csv` | `666b4b80c5a0740863b8a4fd4547a7c3ba1bae8b4b1baee79e532c30877ecd24` |
| `artifacts/policy_bundle/feature_columns.json` | `ebabb1580e95194f227dbe6bda695efe71ea297abeaa6dd07cbc4f9f96d4475b` |
| `artifacts/policy_bundle/model.joblib` | `4d46eb7ae1e2fbfa0b480ff4deeecb1c266280dfbd82dfed85b546c3bbdc78da` |
| `artifacts/policy_bundle/policy_config.json` | `071920f854387245886fd36ecdb8ce9387e5bed2e6e9c077843090eb7a357c57` |
| `artifacts/policy_bundle/value_assumptions.json` | `ce435285516bbc89fe1e774a4edd07c99e3822fd9436b4f6b1011738e2d7977b` |

`manifest.json` is intentionally excluded from its own file-hash map.

## Reproduction

From the repository root:

```bash
generate-synthetic-experiment --rows 10000 --seed 42
generate-experiment-planning
generate-policy-artifact --artifact-version 1.0.0 --seed 42
```

Run the batch scorer independently:

```bash
score-policy-batch \
  --bundle artifacts/policy_bundle \
  --input data/processed/synthetic_experiment.csv \
  --output artifacts/policy_bundle/batch_scores.csv
```

## Audit warning

This artifact is a reproducible offline decision package, not production approval. Training,
evaluation, prospective simulation, and smoke-test scoring use synthetic data. Real-world
randomized validation under the frozen pre-registration is required before serving or treatment
delivery.
