#!/usr/bin/env bash
# Switches the production endpoint selector to the approved version at 100%.
set -euo pipefail

service="${1:-}"
version="${2:-}"
if [ -z "$service" ] || [ -z "$version" ]; then
  echo "Usage: $0 SERVICE VERSION" >&2
  exit 2
fi

bash "$(dirname "$0")/set-endpoint-version.sh" "$service" "$version"
