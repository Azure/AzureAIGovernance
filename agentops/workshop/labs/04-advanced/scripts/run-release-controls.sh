#!/usr/bin/env bash
# Runs both release defenses and returns failure only after both produce evidence.
# Usage: bash scripts/run-release-controls.sh helpdesk-alias 3
set -u

service="${1:?Pass the deployed agent service name.}"
version="${2:?Pass the exact evaluated candidate version.}"
mkdir -p evidence
status=0

if ! bash "$(dirname "$0")/smoke-outlook-status.sh" "$service" "$version"; then
  status=1
fi

if ! python "$(dirname "$0")/critical-case-gate.py" \
  --dataset turns.jsonl \
  --results .agentops/results/latest/results.json \
  --output evidence/critical-case-gate.json; then
  status=1
fi

if [[ "$status" -eq 0 ]]; then
  echo "pass" > evidence/release-controls.status
  echo "Release controls passed."
else
  echo "fail" > evidence/release-controls.status
  echo "Release controls failed. Read the smoke log and critical-case report." >&2
fi
exit "$status"
