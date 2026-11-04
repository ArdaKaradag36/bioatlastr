# Türkiye Bitki DNA Barkod Atlası (Turkey Plant DNA Barcode Atlas)

> **Research question:** Is a short DNA barcode region (rbcL, matK, ITS) enough to distinguish the plant species of
> Türkiye from each other, and where are the data gaps?

```
WCVP (Kew) ─► species.csv ─► ENA (INSDC mirror) ─► FASTA + tables ─► MAFFT + NJ trees + statistics ─► JSON + CSV + figures
 phase 1                       phase 2                              phase 3                            phase 4 (site) · 5 · 6
```

* **No accounts, no API keys, no e-mail.** Default sources: WCVP (species list) and ENA (sequences).
* **No database.** The website reads static JSON files; every number comes from generated data.
* NCBI and GBIF code is kept only as optional sources (`sequence_source: ncbi`, `species_source: gbif`); the default run never contacts them.
* `STATUS.md` always says what is done / running / next (use it to resume).

## Layout

| Path | Content |
|---|---|
| `pipeline/` | Python pipeline: `config*.yaml`, `phase1..6_*.py`, `run_all.py`, `barcode_atlas/` package, `tests/` |
| `data/` | `species.csv`, `species_meta.json`, `synonyms.csv`, `sequence_table.csv`, `sequences/*.fasta`, filter logs; `raw/`, `cache/`, `alignments/` are git-ignored |
| `results/` | CSV summaries, Newick trees, `figures/*.png` |
| `web/` | Next.js (App Router, TypeScript, Tailwind) site; reads `web/public/data/*.json` |
| `docs/rapor_taslagi.md` | Turkish TÜBİTAK-style report draft (generated; placeholders for the biologist) |

## 0. Requirements and install

Python 3.11+, Node.js 20+. Run everything from the repository root.

```bash
python3 -m venv pipeline/.venv
pipeline/.venv/bin/pip install -r pipeline/requirements.txt
```

**MAFFT (no sudo)** – the pipeline looks for `mafft` on `PATH`, then `$MAFFT_BINARY`, then `~/tools/mamba/envs/mafft/bin/mafft`:

```bash
mkdir -p ~/tools && cd ~/tools
curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
MAMBA_ROOT_PREFIX=~/tools/mamba ./bin/micromamba create -y -n mafft -c conda-forge -c bioconda mafft
~/tools/mamba/envs/mafft/bin/mafft --version
```

Without MAFFT a Biopython fallback aligner is used and every output is labelled `fallback (preliminary)`.
Other systems: `sudo apt install mafft` / `brew install mafft`.

## 1. Run the pipeline

Configs: `config.yaml` (full), `config.pilot.yaml` (Fagaceae, Pinaceae, Rosaceae, Lamiaceae), `config.test.yaml` (2 families, 30 species).
Child configs use `base: config.yaml`. Key options: `families_whitelist` (empty = all), `max_species` (empty = all),
`max_per_species_marker` (10), `species_source`, `sequence_source`.

```bash
PY=pipeline/.venv/bin/python
CFG=pipeline/config.pilot.yaml        # or pipeline/config.yaml for everything

$PY pipeline/phase1_species.py   --config $CFG   # WCVP -> data/species.csv, species_meta.json, synonyms.csv (seconds)
$PY pipeline/phase2_sequences.py --config $CFG   # ENA -> data/sequence_table.csv, sequences/*.fasta, logs (long, resumable)
$PY pipeline/run_all.py --config $CFG --skip-phase1 --skip-phase2   # phase 3: align, trees, statistics, JSON + CSV export
$PY pipeline/phase5_figures.py                   # results/figures/*.png
$PY pipeline/phase6_report.py                    # docs/rapor_taslagi.md
```

`python pipeline/run_all.py --config $CFG` runs phases 1-3 in one go. Long runs: start them in the background with a log, e.g.

```bash
nohup scripts/retry.sh 30 $PY pipeline/phase2_sequences.py --config pipeline/config.yaml > logs/full_phase2.log 2>&1 &
```

Every network response is cached in `data/cache/` (retry with exponential back-off on 429/5xx, max 10 requests/s to ENA),
so re-running a phase resumes where it stopped.

What the phases do:

1. **Phase 1** downloads `wcvp.zip` into `data/raw/` (skipped if present; if the download fails the message says which file to place by hand),
   joins `wcvp_names.csv` and `wcvp_distribution.csv` (`|`-separated) on `plant_name_id`, keeps `taxon_rank=Species`, `taxon_status=Accepted`,
   `area_code_l3=TUR` (Türkiye, verified at run time) and drops introduced / extinct / location-doubtful areas and hybrids.
   `endemic=1` when the species is native in exactly one WGSRPD area (TUR). WCVP synonyms are kept for name matching.
2. **Phase 2** resolves each genus (accepted + synonym genera) to an ENA `tax_id`, searches `result=sequence` with
   `tax_tree(<id>)` + marker words + length window, classifies records by marker (spacers, genomes, pseudogenes and multi-marker records are dropped),
   matches names to WCVP accepted names / synonyms (unmatched names are logged in `data/unmatched_names.csv`), downloads FASTA in batches, applies
   sequence filters (length, N fraction), limits identical copies, and keeps at most 10 sequences per species and marker (Türkiye specimens first).
   `data/ena_filter_summary.csv` has raw / kept / dropped counts per marker and reason. Every Turkish species stays in the coverage table, also with zero sequences.
3. **Phase 3** aligns per marker and family (families with more than `max_group_sequences` sequences genus by genus; groups with too few sequences are skipped and logged in
   `results/skipped_groups.csv`), builds NJ trees, computes coverage, best-close-match discrimination per marker, species-level discrimination per marker
   and marker combination, zero-distance pairs, nearest relatives and data gaps, then writes `web/public/data/*.json` and `results/*.csv`.

## 2. Tests

```bash
cd pipeline && .venv/bin/python -m pytest -q tests      # filters, name matching, ENA helpers, WCVP rules, discrimination
cd web && npm test                                      # TypeScript helpers
```

## 3. Website

```bash
cd web
npm install
npm run dev          # http://localhost:3000
npm run build && npm run start
```

Pages (Turkish UI): home (headline numbers) · `/turler` search with autocomplete (Latin + Turkish names) · `/turler/<species>`
(markers, ENA/GenBank links, sequence viewer + FASTA, 5 nearest relatives, tree with the species highlighted; species without sequences show relatives that have data) ·
`/agaclar` tree explorer (zoom/pan) · `/veri-bosluklari` data gaps · `/dizi-ara` browser-side sequence search (indicative) · `/yontem` methods and limitations.
After new pipeline data, run phase 3 again and `npm run build`. Species details are sharded by genus (`web/public/data/species/<genus>.json`)
so the deployment has a few thousand files; species pages are rendered on first request.

## 4. Deploy to Vercel (free)

The pipeline runs on your own computer; the site only needs the generated JSON in `web/public/data/` (about 63 MB, tracked in git,
no file above 6 MB). Nothing outside `web/` is read at build time. No environment variables, accounts or API keys are needed.

**First deployment (Git integration, free Hobby plan)**

1. Create an empty GitHub repository and push: `git remote add origin <url> && git push -u origin main` (the public history was created fresh; the pre-clean history stays only in your local branch `backup-private`, **never push that branch**)
   (check first: `scripts/check_large_files.sh`).
2. <https://vercel.com/new> → *Import Git Repository* → select the repository.
3. **Root Directory = `web`** (Edit next to the project name). Framework preset: *Next.js* (detected). Build command, output
   directory and install command stay at their defaults (`npm run build`, `.next`, `npm install`). Click *Deploy*.
4. Open the `*.vercel.app` URL and check: home numbers, a species page, `/agaclar`, `/dizi-ara`.
   Optional: *Settings → Domains* to add your own domain.

Deploying through Git has no 100 MB upload limit (the CLI upload limit on the Hobby plan is 100 MB of source and 15,000 files; the repo
is ≈ 73 MB). The Hobby plan is for non-commercial use only.

**Republish after the data changed**

```bash
# 1. re-run the pipeline into runs/full and validate (resumable; see section 1), then publish into web/public/data:
scripts/publish_full.sh                 # validates, backs up the old data, copies runs/full/*, removes voucher/collector text (sanitize_public.py), re-adds open Turkish names
#    after changing names: scripts/names_rebuild.sh   (open licences only by default)
# 2. check the site locally
cd web && npm run build && npx next start -p 3200      # browse http://localhost:3200
# 3. commit and push: Vercel builds and deploys the new version automatically
cd .. && scripts/check_large_files.sh && git add -A && git commit -m "Update data" && git push
```

Rollback: in the Vercel dashboard open *Deployments* → an older deployment → *Promote to Production*.

Optional NCBI source (disabled by default): `export NCBI_EMAIL=you@example.org` (and `NCBI_API_KEY=...`); the config files never contain them.

## 5. Photo identification later

Not implemented. `web/src/lib/identification.ts` defines the contract (`PhotoIdentifier`); add `web/src/app/api/identify/route.ts`
and link candidates to `/turler/<slug>`. The site uses normal Next.js output (no static export), so API routes work on Vercel.

## 6. Limitations

See `/yontem`. Record names are not verified (misidentified records), species with other names in ENA look "missing", comparisons are within a family
(or genus for very large families), small samples make per-species results uncertain, p-distance + NJ are simple methods.

## 7. Turkish common names (open licences only)

Names are never typed by hand: `scripts/names_fetch.py wikidata|gbif|inat` (cached, polite rate) → `scripts/names_build.py` →
`data/names/turkish_names.csv` (rank, latin_name, turkish_name, source, source_id_or_url, license, license_class, source_tier, matched_via, ambiguous) and
`exports/*` → `scripts/names_to_web.py` adds them to `web/public/data` (also run by `scripts/publish_full.sh`). Latin-name exports: `scripts/export_taxa.py`.

**Published sources (all tier A, open):** Wikidata (CC0), Vikipedi tr titles (CC BY-SA), Catalogue of Life via GBIF (CC BY 4.0), Cichorieae Systematics Portal (CC BY 4.0).
The names table as a whole is CC BY-SA 4.0. **Not published:** iNaturalist and IUCN (non-commercial), GRIN (licence unverified), marine registers / DAISIE / railway EIA dataset (tier C).
`names.include_non_commercial` in `pipeline/config.yaml` is `false`; the removed non-commercial and tier C rows go to the git-ignored `data/names/private/`
so a biologist can check them locally (never publish them). Per-source evidence: `docs/licence_audit.md`; licences/attribution: `LICENSE` (MIT, code), `DATA_LICENSE.md`,
`THIRD_PARTY_NOTICES.md`, `CITATION.cff`, `data/names/LICENSES.md`, site page `/kaynaklar`. Review sample for the biologist: `exports/turkish_names_check_sample.csv`.
Names are not expert-verified; ambiguous names are flagged ("birden fazla türe verilen halk adı").

## 8. Privacy and placeholders

The site has no analytics, cookies or trackers; the sequence search runs in the browser only. Voucher/collector strings, locality text and submitter details
are removed from published sequence records (`scripts/sanitize_public.py`). Before publishing fill in the placeholders (search for `PLACEHOLDER_`):
`PLACEHOLDER_CONTACT_EMAIL` (`web/src/lib/site.ts`, `DATA_LICENSE.md`), `PLACEHOLDER_GITHUB_REPO_URL` (`web/src/lib/site.ts`, `CITATION.cff`),
`PLACEHOLDER_AUTHOR_NAME` (`LICENSE`), `PLACEHOLDER_SURNAME` / `PLACEHOLDER_GIVEN_NAME` (`CITATION.cff`).
