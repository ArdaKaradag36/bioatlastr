# STATUS (updated 2026-11-03)

**Done:** WCVP Türkiye list (10,007 species) · ENA retrieval (1,624 genera, 277,971 records, 27,823 kept) · MAFFT alignments / NJ trees /
discrimination (727 groups, 0 timeouts) · full run published to `web/public/data` · site built and browser-checked (home, search,
species pages, trees, gaps, sequence search, method) · report draft `docs/rapor_taslagi.md`.

**In progress:** nothing running. Vercel deployment NOT done (waiting for confirmation).

**Next (human):** biologist fills the `BİYOLOG TARAFINDAN DOLDURULACAK` blocks in the report; advisor review; deploy (Vercel, Root Directory = `web`).

## Commands
- Tests: `pipeline/.venv/bin/python -m pytest pipeline/tests -q`; `cd web && npm test`
- Full re-run (resumable, isolated in `runs/full`): `touch data/.confirm_full_run && (setsid nohup systemd-inhibit --what=sleep:idle scripts/full_run.sh > logs/full_run.log 2>&1 &)`; progress: `tail -3 logs/full_run.log` (ends with FULL_RUN_DONE)
- Publish a validated full run: `scripts/publish_full.sh && (cd web && npm run build)`
- Pilot (4 families): `scripts/pilot_refresh.sh`
- Site locally: `cd web && npm run build && npx next start -p 3200`; browser check: `pipeline/.venv/bin/python scripts/site_check.py`; sizes: `scripts/site_perf.py`
- Unmatched-name sample: `pipeline/.venv/bin/python scripts/unmatched_sample.py 200`

## Turkish names (tiers/licences)
Published Turkish names: open licences only (2,658 species, 26.6%; 325 genera; 528 endemics). Non-commercial and tier C rows are in the git-ignored data/names/private/. Not expert-verified.
