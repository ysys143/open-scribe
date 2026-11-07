#!/bin/bash
set -euo pipefail
scribe_source="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scribe_python=python3
scribe_venv=""
scribe_upgrade=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) scribe_python="$2"; shift 2;;
    --venv) scribe_venv="$2"; shift 2;;
    --upgrade) scribe_upgrade=1; shift;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2;;
  esac
done
exec "$scribe_python" "$scribe_source/scripts/install.py" "$scribe_source" "$scribe_venv" "$scribe_upgrade"
