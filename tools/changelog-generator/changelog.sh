#!/usr/bin/env bash
# Run from any directory; output defaults to CHANGELOG.md in the current directory.
set -u
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/changelog.py" "$@"
