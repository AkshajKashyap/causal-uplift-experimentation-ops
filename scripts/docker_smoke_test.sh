#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-causal-uplift-experimentation-ops:smoke}"

printf '==> Building %s\n' "${IMAGE_NAME}"
docker build --tag "${IMAGE_NAME}" .

printf '==> Checking package import and metadata commands\n'
docker run --rm "${IMAGE_NAME}" \
  python -c "import causal_uplift_experimentation_ops as package; print(package.__version__)"
docker run --rm "${IMAGE_NAME}" causal-uplift-ops --version
docker run --rm "${IMAGE_NAME}" causal-uplift-ops project-info

printf '==> Running compact container tests\n'
docker run --rm "${IMAGE_NAME}" \
  python -m pytest tests/test_data_generation.py tests/test_packaging.py

printf '==> Generating data and a policy artifact inside the container\n'
docker run --rm "${IMAGE_NAME}" sh -c \
  "generate-synthetic-experiment --rows 1000 --seed 42 && generate-policy-artifact"

printf 'Docker smoke test completed successfully.\n'
