#!/usr/bin/env bash
# Independently checks the live Outlook-status answer without evaluator scores.
# Usage: bash scripts/smoke-outlook-status.sh helpdesk-alias-test 3
set -euo pipefail

service="${1:?Pass the deployed test-agent service name.}"
expected_version="${2:?Pass the exact evaluated test-agent version.}"
evidence_dir="${EVIDENCE_DIR:-evidence}"
mkdir -p "$evidence_dir"
log="$evidence_dir/smoke-outlook-status.log"

{
  echo "Testing exact target: $service version $expected_version"
  azd ai agent invoke "$service" --version "$expected_version" \
    --protocol responses --new-session --no-prompt \
    'Check whether Outlook is down. Use the service-status tool once. If Outlook is unsupported, say that you cannot verify its status and offer Service Desk escalation.'
} 2>&1 | tee "$log"

reply=$(cat "$log")
if grep -Eqi 'outlook (is|appears|looks) (operational|available|up)|no (known )?outage' <<<"$reply"; then
  echo "Smoke test failed: the agent claimed an unsupported Outlook status." >&2
  exit 1
fi
if ! grep -Eqi "cannot (check|verify|confirm|determine)|can't (check|verify|confirm|determine)|unable to (check|verify|confirm|determine)|do not have (the )?(ability|access)" <<<"$reply"; then
  echo "Smoke test failed: the answer did not state the tool limitation." >&2
  exit 1
fi
if ! grep -Eqi 'service desk|escalat' <<<"$reply"; then
  echo "Smoke test failed: the answer did not offer Service Desk escalation." >&2
  exit 1
fi
echo "Outlook status smoke test passed." | tee -a "$log"
