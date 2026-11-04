#!/usr/bin/env bash
# Prints the version number of an agent service that azd has deployed.
# Usage: bash scripts/agent-version.sh helpdesk-ALIAS
set -euo pipefail

service="${1:-}"
if [ -z "$service" ]; then
  echo "Usage: $0 SERVICE" >&2
  exit 2
fi
key=$(echo "$service" | tr 'a-z-' 'A-Z_')
version=$(azd env get-value "AGENT_${key}_VERSION" 2>/dev/null || true)

if [ -z "$version" ]; then
  version=$(azd ai agent show "$service" --output json --no-prompt \
    | python -c 'import json,sys
def find(value):
    if isinstance(value, dict):
        if value.get("version") is not None:
            return str(value["version"])
        for child in value.values():
            found = find(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find(child)
            if found:
                return found
    return ""
print(find(json.load(sys.stdin)))')
fi

if [ -z "$version" ]; then
  echo "Cannot read the deployed version of $service" >&2
  exit 1
fi
echo "$version"
