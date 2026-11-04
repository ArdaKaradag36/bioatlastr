#!/usr/bin/env bash
# Pilot (4 families): phases 1-3 + figures + report. Log: logs/pilot_run.log
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python; CFG=pipeline/config.pilot.yaml
date +%T
$PY pipeline/phase1_species.py --config $CFG || exit 1
scripts/retry.sh 10 $PY pipeline/phase2_sequences.py --config $CFG || exit 1
$PY pipeline/run_all.py --config $CFG --skip-phase1 --skip-phase2 || exit 1
$PY pipeline/phase5_figures.py && $PY pipeline/phase6_report.py
date +%T; echo PILOT_DONE
