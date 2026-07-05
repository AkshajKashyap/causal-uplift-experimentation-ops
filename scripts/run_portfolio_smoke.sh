#!/usr/bin/env bash
set -euo pipefail

section() {
  printf '\n==> %s\n' "$1"
}

section "Generate deterministic synthetic experiment data"
generate-synthetic-experiment --rows 10000 --seed 42

section "Generate baseline A/B report"
generate-ab-report

section "Generate cross-fitted model comparison"
generate-crossfit-comparison

section "Freeze and score the selected policy artifact"
generate-policy-artifact --artifact-version 1.0.0 --seed 42

section "Generate staging API documentation"
generate-api-staging-report

section "Generate deterministic audit smoke events"
generate-api-audit-smoke-log

section "Run offline observability and promotion gates"
generate-staging-observability

section "Run tests and lint"
make check

printf '\nPortfolio smoke workflow completed successfully.\n'
