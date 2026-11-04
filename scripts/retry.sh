#!/usr/bin/env bash
# Usage: scripts/retry.sh <max_attempts> <command...>   (re-runs a resumable phase until it succeeds)
# Stops early with FULL_RUN_FAILED when the same traceback appears twice in a row (deterministic bug).
n=$1; shift
prev=""
for i in $(seq 1 "$n"); do
  echo "=== attempt $i $(date +%T)"
  tmp=$(mktemp)
  "$@" 2> >(tee "$tmp" >&2) && { rm -f "$tmp"; echo "=== OK $(date +%T)"; exit 0; }
  sleep 1  # let the stderr tee finish
  sig=$(grep -A200 Traceback "$tmp" | tail -4 | md5sum | cut -d' ' -f1); has=$(grep -c Traceback "$tmp"); rm -f "$tmp"
  if [ "$has" -gt 0 ] && [ "$sig" = "$prev" ]; then
    echo "=== same traceback twice in a row: deterministic error, not retrying"; echo "FULL_RUN_FAILED (repeated traceback)"; exit 1
  fi
  [ "$has" -gt 0 ] && prev=$sig
  sleep 120
done
echo "=== FAILED after $n attempts"; echo "FULL_RUN_FAILED"; exit 1
