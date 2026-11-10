# Changelog

Public notes for this research project. This is not a software-release log for third-party installers.

## Unreleased

## 0.3.0 — 2026-11-10

- New site pages: `/oncelik` (sequencing priority lists) and `/rehber` (family-level marker guide).
- Multi-marker rows use `strict_combined_distance`: mean of shared-marker species p-distances, only species present in every marker of the combination (n reported), same species-level nearest-neighbour rule (not the intersection of per-marker successes). Same-subset single-marker columns added for fair comparison.
- Marker guide recommendations require Holm-corrected significance (McNemar pairs within family/genus).
- `genera_unresolved` labelled as all unresolved WCVP genus strings; split into accepted vs synonym-only counts in meta and `/yontem`.
- Full-run reproducibility inputs committed: `data/species_full.csv`, `data/species_meta_full.json`, `data/config_full.yaml`.
- Accessibility report for Playwright + axe on main pages, including `/oncelik` and `/rehber` (`docs/accessibility.md`).

## 0.2.0 — 2026-11-04

- Official success definition is the strict, threshold-free nearest-neighbour test (every evaluated sequence of a species must pass). Multi-marker combination rows later moved to `strict_combined_distance` (see 0.3.0).
- Non-binomial WCVP names (for example `Taraxacum sect. Taraxacum`) are dropped from the species list.
- Exact DNA strings shared across families are flagged `suspect: true`, excluded from discrimination, and shown on species pages.
- Public identity: authors Arda Karadağ and Buse Menekşe; contact and repository fields live in `web/src/lib/site.ts`.
- Public site is published at https://ardakaradag36.github.io/bioatlastr/ .
- Citation (`CITATION.cff`), Zenodo metadata (`.zenodo.json`), contributing and changelog files added.

## 0.1.0 — 2026-11-04

- First public snapshot of the pipeline (WCVP + ENA, MAFFT, p-distance, NJ) and the Turkish-language website.
