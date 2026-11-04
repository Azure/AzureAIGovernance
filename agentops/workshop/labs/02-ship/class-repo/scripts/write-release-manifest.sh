#!/usr/bin/env bash
# Records the evaluated and released identities, versions, source fingerprint,
# and pipeline provenance after the exact released version passes its smoke test.
# Usage: bash scripts/write-release-manifest.sh TEST_SERVICE TEST_VERSION RELEASE_SERVICE RELEASE_VERSION OUTPUT
set -euo pipefail

test_service="${1:-}"
test_version="${2:-}"
release_service="${3:-}"
release_version="${4:-}"
output="${5:-release-manifest.json}"
if [ -z "$test_service" ] || [ -z "$test_version" ] || \
   [ -z "$release_service" ] || [ -z "$release_version" ]; then
  echo "Usage: $0 TEST_SERVICE TEST_VERSION RELEASE_SERVICE RELEASE_VERSION [OUTPUT]" >&2
  exit 2
fi

commit="${RELEASE_COMMIT:-$(git rev-parse HEAD)}"
fingerprint="${RELEASE_SOURCE_SHA256:-$(git archive "$commit" -- azure.yaml agentops.yaml src/helpdesk scripts | sha256sum | awk '{print $1}')}"
created_at="${RELEASE_CREATED_AT:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
pipeline_url="${RELEASE_PIPELINE_URL:-unknown}"
extension_version="${AZD_AI_AGENTS_EXTENSION_VERSION:-1.0.0-beta.23}"

export test_service test_version release_service release_version output
export commit fingerprint created_at pipeline_url extension_version
python - <<'PY'
import json
import os
from pathlib import Path

manifest = {
    "schema_version": 1,
    "created_at_utc": os.environ["created_at"],
    "promotion": {
        "mode": "rebuild-from-reviewed-source",
        "exact_version_promotion": False,
        "claim": (
            "The two agents are distinct identities with independently assigned "
            "versions. Equivalence is established at source and configuration "
            "level by the commit and fingerprint, not by claiming one immutable "
            "runtime artifact was promoted."
        ),
    },
    "evaluated": {
        "service": os.environ["test_service"],
        "version": os.environ["test_version"],
    },
    "released": {
        "service": os.environ["release_service"],
        "version": os.environ["release_version"],
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
