#!/usr/bin/env bash
# Deploys one help desk agent to the existing class Foundry project and prints
# the version number Foundry assigned to it. Creates no Azure resources.
# Usage: bash scripts/deploy-agent.sh helpdesk-alias-test
set -euo pipefail

service="$1"
: "${AZURE_ENV_NAME:=dev}"

# azd progress goes to the log; only the version number goes to the output.
{
  bash "$(dirname "$0")/configure-azd.sh"
  azd deploy "$service" --no-prompt
} >&2

bash "$(dirname "$0")/agent-version.sh" "$service"
