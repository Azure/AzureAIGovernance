#!/usr/bin/env bash
# Pins the agent endpoint to one exact version at 100 percent.
set -euo pipefail

service="${1:-}"
version="${2:-}"
if [ -z "$service" ] || [ -z "$version" ]; then
  echo "Usage: $0 SERVICE VERSION" >&2
  exit 2
fi

python - "$service" "$version" <<'PY'
from pathlib import Path
import re
import sys

service, version = sys.argv[1:]
path = Path("azure.yaml")
text = path.read_text(encoding="utf-8")
pattern = r'(agentVersion:\s*")[^"]+(")'
updated, count = re.subn(pattern, rf'\g<1>{version}\g<2>', text, count=1)
if count != 1:
    raise SystemExit(f"Cannot find the endpoint selector for {service}.")
path.write_text(updated, encoding="utf-8", newline="\n")
PY

azd ai agent endpoint update "$service" --no-prompt
azd ai agent endpoint show "$service" --output json --no-prompt
