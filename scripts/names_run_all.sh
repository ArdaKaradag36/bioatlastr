#!/usr/bin/env bash
# Turkish-name pipeline after the fetchers started: inat fetch -> build -> site data -> tests -> site build. Log: logs/names_run_all.log
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python
echo "start $(date +%T)"
until grep -q WIKIDATA_DONE logs/names_wikidata.log; do sleep 20; done; echo "wikidata done $(date +%T)"
$PY scripts/names_fetch.py inat > logs/names_inat.log 2>&1; echo "inat done $(date +%T)"
until grep -q GBIF_DONE logs/names_gbif.log; do sleep 20; done; echo "gbif done $(date +%T)"
$PY scripts/names_build.py > logs/names_build.log 2>&1 || { echo "NAMES_BUILD_FAILED"; exit 1; }
cat logs/names_build.log
$PY scripts/names_to_web.py || { echo "NAMES_TO_WEB_FAILED"; exit 1; }
$PY -m pytest pipeline/tests -q 2>&1 | tail -n 2
(cd web && npm test 2>&1 | grep -E "^# (pass|fail)"; npm run build > ../logs/names_web_build.log 2>&1; echo "web build exit $?")
echo "index gz bytes: $(gzip -c web/public/data/species_index.json | wc -c) (raw $(wc -c < web/public/data/species_index.json)); taxon_names gz $(gzip -c web/public/data/taxon_names.json | wc -c)"
echo NAMES_PIPELINE_DONE
