# Reproducibility

## Environment setup

The supported baseline is Python 3.11 or 3.12 on an Ubuntu-like environment.

```bash
git clone <repository-url>
cd causal-uplift-experimentation-ops
python -m venv .venv
source .venv/bin/activate
make install
```

`make install` performs an editable installation with the `dev` extra, which includes pytest,
Ruff, and the HTTP client used by FastAPI tests. Runtime dependencies remain in the base package.

Confirm the installed package:

```bash
causal-uplift-ops --version
causal-uplift-ops project-info
```

## Makefile commands

| Command | Purpose |
| --- | --- |
| `make install` | Install the package and development tools |
| `make test` | Run the full pytest suite |
| `make lint` | Run Ruff |
| `make check` | Run tests and Ruff |
| `make generate-data` | Recreate the seeded synthetic experiment |
| `make reports` | Recreate the main analysis, policy, and planning reports |
| `make artifact` | Freeze the selected model/policy bundle and batch scores |
| `make api-report` | Recreate staging API and safety documentation |
| `make observability` | Generate audit smoke data and the promotion report |
| `make smoke` | Run the compact portfolio workflow and quality checks |
| `make clean` | Remove caches and ignored generated data/model outputs |

## Deterministic workflow

The quickest full verification is:

```bash
make smoke
```

It regenerates the default 10,000-row dataset with seed 42, the A/B report, the cross-fitted
comparison, the selected policy artifact, API documentation, deterministic audit events, and the
staging observability report before running tests and lint.

Individual report commands expose their seed, fold, bootstrap, and path options. Defaults are
fixed in code and shown in each CLI's `--help`.

## Seeds and fingerprints

- Synthetic data defaults to seed 42.
- Train/test splits, cross-fitting, bootstraps, and trial simulation use explicit seeds.
- `manifest.json` records the package version, dataset fingerprint, feature-contract fingerprint,
  configuration fingerprint, and hashes of artifact files.
- The policy configuration includes its model, decision rule, economics, evidence paths, and
  random seed.
- Creation timestamps can change when an artifact is rebuilt; stable fingerprints intentionally
  exclude the timestamp where appropriate.

Rebuilding with equivalent code, inputs, and configuration should reproduce the dataset and
scoring outputs. Serialized model-file bytes can vary across Python or dependency versions, so
the environment and manifest should be reviewed together.

## Generated and ignored files

The following are intentionally regenerated and ignored by Git:

- `data/processed/`
- `artifacts/**/*.joblib`
- `artifacts/**/batch_scores.csv`
- `artifacts/**/*.jsonl`
- virtual environments, caches, bytecode, and package metadata directories

Human-readable reports, artifact configuration, and manifests are retained for portfolio review.
Run `git status` after generation to distinguish documented report refreshes from ignored runtime
outputs.

## Docker

Build and run the metadata command:

```bash
docker build -t causal-uplift-experimentation-ops .
docker run --rm causal-uplift-experimentation-ops
```

Run the container verification:

```bash
bash scripts/docker_smoke_test.sh
```

The image is CPU-only and uses Python 3.12. Docker support proves packaging portability; it is not
a deployment architecture.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests using Python 3.12. It installs the
editable package with development tools, runs Ruff and pytest, and executes a compact CLI flow
through data generation, A/B analysis, artifact freezing, API reporting, audit generation, and
observability.
