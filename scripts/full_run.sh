#!/usr/bin/env bash
# FULL run, isolated in runs/full (site data in web/public/data is NOT touched):
#   phase 1 -> phase 2 (resumable, retried) -> phase 3 -> figures -> report -> validation.
# Log: logs/full_run.log (ends with FULL_RUN_DONE).  Publish afterwards with scripts/publish_full.sh.
# Needs data/.confirm_full_run (created by the user).  Re-running resumes from the disk caches / alignments.
cd "$(dirname "$0")/.."
export BARCODE_RUN_DIR=runs/full
PY=pipeline/.venv/bin/python
CFG=pipeline/config.yaml
mkdir -p runs/full logs
echo "FULL_RUN_START $(date '+%F %T')"
$PY pipeline/phase1_species.py --config $CFG || { echo "FULL_RUN_FAILED phase1"; exit 1; }
scripts/retry.sh 40 $PY pipeline/phase2_sequences.py --config $CFG || { echo "FULL_RUN_FAILED phase2"; exit 1; }
echo "PHASE2_DONE $(date '+%F %T')"
$PY pipeline/run_all.py --config $CFG --skip-phase1 --skip-phase2 || { echo "FULL_RUN_FAILED phase3"; exit 1; }
echo "PHASE3_DONE $(date '+%F %T')"
$PY pipeline/phase5_figures.py && $PY pipeline/phase6_report.py
$PY scripts/validate_full.py && echo "VALIDATION_OK (run scripts/publish_full.sh to publish)" || echo "VALIDATION_FAILED (nothing published)"
echo "FULL_RUN_END $(date '+%F %T')"; echo FULL_RUN_DONE
