#!/usr/bin/env bash
# Invokes one exact deployed version and checks the observable result of the
# create_ticket tool. The version argument prevents a test of a later version.
# Usage: bash scripts/smoke-test.sh helpdesk-alias 3
set -euo pipefail

service="${1:-}"
expected_version="${2:-}"
if [ -z "$service" ] || [ -z "$expected_version" ]; then
  echo "Usage: $0 SERVICE EXPECTED_VERSION" >&2
  exit 2
fi

selected_version=$(bash "$(dirname "$0")/read-endpoint-selector.sh" "$service" \
  "${SELECTOR_EVIDENCE_FILE:-selected-selector.json}")
if [ "$selected_version" != "$expected_version" ]; then
  echo "Smoke test stopped: $service endpoint selects version $selected_version, not expected version $expected_version." >&2
  exit 1
fi
echo "Testing exact target: $service version $expected_version"

reply=$(azd ai agent invoke "$service" --version "$expected_version" \
  --protocol responses --new-session --no-prompt \
  'VPN reconnect and sign-in failed. Check service status and create a VPN ticket.')
echo "$reply"

if ! grep -qi 'network support' <<<"$reply" || ! grep -qi 'SIM-VPN-001' <<<"$reply"; then
  echo "Smoke test failed: the create_ticket result did not contain queue Network Support and reference SIM-VPN-001." >&2
  exit 1
fi
echo "Smoke test passed for $service version $expected_version."
