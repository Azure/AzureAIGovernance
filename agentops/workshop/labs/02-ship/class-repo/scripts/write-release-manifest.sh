#!/usr/bin/env bash
# Records the evaluated and promoted version, previous selector, source
# fingerprint and pipeline provenance after the exact version passes smoke.
# Usage: bash scripts/write-release-manifest.sh SERVICE VERSION PREVIOUS_SELECTOR OUTPUT
set -euo pipefail

service="${1:-}"
version="${2:-}"
previous_selector="${3:-}"
output="${4:-release-manifest.json}"
if [ -z "$service" ] || [ -z "$version" ] || [ -z "$previous_selector" ]; then
  echo "Usage: $0 SERVICE VERSION PREVIOUS_SELECTOR [OUTPUT]" >&2
  exit 2
fi

commit="${RELEASE_COMMIT:-$(git rev-parse HEAD)}"
fingerprint="${RELEASE_SOURCE_SHA256:-$(git archive "$commit" -- azure.yaml agentops.yaml src/helpdesk scripts | sha256sum | awk '{print $1}')}"
created_at="${RELEASE_CREATED_AT:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
pipeline_url="${RELEASE_PIPELINE_URL:-unknown}"
extension_version="${AZD_AI_AGENTS_EXTENSION_VERSION:-1.0.0-beta.23}"

export service version previous_selector output
export commit fingerprint created_at pipeline_url extension_version
python - <<'PY'
import json
import os
from pathlib import Path

previous = json.loads(Path(os.environ["previous_selector"]).read_text(encoding="utf-8"))
manifest = {
    "schema_version": 1,
    "created_at_utc": os.environ["created_at"],
    "promotion": {
        "mode": "single-agent-version-selector",
        "exact_version_promotion": True,
        "selected_traffic_percentage": 100,
        "previous_selector": previous,
        "rollback": "Restore previous_selector and run azd ai agent endpoint update.",
    },
    "evaluated": {
        "service": os.environ["service"],
        "version": os.environ["version"],
    },
    "released": {
        "service": os.environ["service"],
        "version": os.environ["version"],
        "smoke_test": "passed",
        "tool_evidence": {
            "queue": "Network Support",
            "ticket_reference": "SIM-VPN-001",
        },
    },
    "provenance": {
        "git_commit": os.environ["commit"],
        "source_configuration_sha256": os.environ["fingerprint"],
        "pipeline_url": os.environ["pipeline_url"],
        "azd_ai_agents_extension": os.environ["extension_version"],
    },
}
path = Path(os.environ["output"])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(path)
PY
