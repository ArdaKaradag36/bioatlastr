#!/usr/bin/env bash
# Re-run the pilot (4 families) from cache with the current code. Log: logs/pilot_refresh.log
cd "$(dirname "$0")/.."
PY=pipeline/.venv/bin/python; CFG=pipeline/config.pilot.yaml
date +%T
$PY pipeline/phase1_species.py --config $CFG && scripts/retry.sh 10 $PY pipeline/phase2_sequences.py --config $CFG \
 && $PY pipeline/run_all.py --config $CFG --skip-phase1 --skip-phase2 && $PY pipeline/phase5_figures.py && $PY pipeline/phase6_report.py
date +%T; echo PILOT_REFRESH_DONE
