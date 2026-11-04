#!/usr/bin/env bash
# Saves the current endpoint version selector and prints its selected version.
# The workshop contract requires one FixedRatio rule at 100 percent.
set -euo pipefail

service="${1:-}"
output="${2:-previous-selector.json}"
if [ -z "$service" ]; then
  echo "Usage: $0 SERVICE [OUTPUT]" >&2
  exit 2
fi

endpoint_json=$(azd ai agent endpoint show "$service" --output json --no-prompt)
export endpoint_json
python - "$output" <<'PY'
import json
import os
import sys
from pathlib import Path

data = json.loads(os.environ["endpoint_json"])

def find_rules(value):
    if isinstance(value, dict):
        for key in ("versionSelectionRules", "version_selection_rules"):
            if key in value:
                return value[key]
        for child in value.values():
            found = find_rules(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_rules(child)
            if found is not None:
                return found
    return None

rules = find_rules(data)
if not isinstance(rules, list) or len(rules) != 1:
    raise SystemExit("Endpoint must have exactly one selected production version.")
rule = rules[0]
version = rule.get("agentVersion", rule.get("agent_version"))
percentage = rule.get("trafficPercentage", rule.get("traffic_percentage"))
if not version or int(percentage) != 100:
    raise SystemExit("Endpoint selector must route 100 percent to one version.")
selector = {
    "versionSelectionRules": [{
        "type": rule.get("type", "FixedRatio"),
        "agentVersion": str(version),
        "trafficPercentage": 100,
    }]
}
Path(sys.argv[1]).write_text(json.dumps(selector, indent=2) + "\n", encoding="utf-8")
print(version)
PY
