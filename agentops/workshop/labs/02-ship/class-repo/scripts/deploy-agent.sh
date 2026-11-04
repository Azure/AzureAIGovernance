#!/usr/bin/env bash
# Keeps production on its current selected version, deploys one candidate under
# the same agent identity, and prints the candidate version. On the first run,
# it creates a baseline version before deploying the candidate.
# Usage: bash scripts/deploy-agent.sh helpdesk-alias candidate-version.txt previous-selector.json
set -euo pipefail

service="${1:-}"
candidate_file="${2:-candidate-version.txt}"
selector_file="${3:-previous-selector.json}"
if [ -z "$service" ]; then
  echo "Usage: $0 SERVICE [CANDIDATE_FILE] [SELECTOR_FILE]" >&2
  exit 2
fi
: "${AZURE_ENV_NAME:=dev}"
script_dir=$(cd "$(dirname "$0")" && pwd)

bash "$script_dir/configure-azd.sh" >&2

if ! bash "$script_dir/read-endpoint-selector.sh" "$service" "$selector_file" >/dev/null 2>&1; then
  original=$(cat azure.yaml)
  trap 'printf "%s" "$original" > azure.yaml' EXIT
  python - "$service" <<'PY'
from pathlib import Path
import re
import sys

service = sys.argv[1]
path = Path("azure.yaml")
text = path.read_text(encoding="utf-8")
text = text.replace("HELPDESK_VARIANT: candidate", "HELPDESK_VARIANT: baseline")
text = re.sub(
    r"\n        agentEndpoint:\n(?:            .*\n|                .*\n|                    .*\n|                      .*\n)+(?=        protocols:)",
    "\n",
    text,
    count=1,
)
path.write_text(text, encoding="utf-8", newline="\n")
PY
  azd deploy "$service" --no-prompt >&2
  stable_version=$(bash "$script_dir/agent-version.sh" "$service")
  printf "%s" "$original" > azure.yaml
  trap - EXIT
  bash "$script_dir/set-endpoint-version.sh" "$service" "$stable_version" >&2
  bash "$script_dir/read-endpoint-selector.sh" "$service" "$selector_file" >/dev/null
fi

stable_version=$(python - "$selector_file" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print(data["versionSelectionRules"][0]["agentVersion"])
PY
)
bash "$script_dir/set-endpoint-version.sh" "$service" "$stable_version" >/dev/null
azd deploy "$service" --no-prompt >&2
candidate_version=$(bash "$script_dir/agent-version.sh" "$service")
printf '%s\n' "$candidate_version" > "$candidate_file"

echo "$candidate_version"
