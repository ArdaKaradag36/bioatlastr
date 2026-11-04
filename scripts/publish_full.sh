#!/usr/bin/env bash
# Copy the validated full-run outputs over the published pilot data (web/public/data, results, docs).
cd "$(dirname "$0")/.."
pipeline/.venv/bin/python scripts/validate_full.py || { echo "not publishing"; exit 1; }
rm -rf web/public/data.pilot_backup && cp -r web/public/data web/public/data.pilot_backup
rm -rf web/public/data && cp -r runs/full/web_data web/public/data
rm -rf results.pilot_backup && cp -r results results.pilot_backup && rm -rf results && cp -r runs/full/results results
cp runs/full/docs/rapor_taslagi.md docs/rapor_taslagi.md
pipeline/.venv/bin/python scripts/sanitize_public.py   # remove voucher/collector names and locality text (personal data)
[ -f data/names/turkish_names.csv ] && pipeline/.venv/bin/python scripts/names_to_web.py   # re-add Turkish names to the fresh site data
echo "published. Rebuild the site: cd web && npm run build   (pilot backups: web/public/data.pilot_backup, results.pilot_backup)"
