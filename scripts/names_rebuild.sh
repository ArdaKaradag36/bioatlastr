#!/usr/bin/env bash
# Rebuild Turkish names from the cache and refresh the site data.
#   default (open licences only, names.include_non_commercial: false in pipeline/config.yaml):  scripts/names_rebuild.sh
#   LOCAL PREVIEW with non-commercial names (never publish!):  NAMES_INCLUDE_NON_COMMERCIAL=1 scripts/names_rebuild.sh
# After a flag change rebuild from the published data: scripts/publish_full.sh re-adds the names; or run `cd web && rm -rf .next && npm run build`.
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
$PY scripts/names_build.py && $PY scripts/names_to_web.py && (cd web && rm -rf .next && npm run build)
