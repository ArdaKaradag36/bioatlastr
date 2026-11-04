# Changelog

Public notes for this research project. This is not a software-release log for third-party installers.

## 0.2.0 — 2026-11-04

- Official success definition is the strict, threshold-free nearest-neighbour test (every evaluated sequence of a species must pass). Multi-marker combination rows are labelled as a looser, different definition.
- Non-binomial WCVP names (for example `Taraxacum sect. Taraxacum`) are dropped from the species list.
- Exact DNA strings shared across families are flagged `suspect: true`, excluded from discrimination, and shown on species pages.
- Public identity: authors Arda Karadağ and Buse Menekşe; contact and repository fields live in `web/src/lib/site.ts`.
- Citation (`CITATION.cff`), Zenodo metadata (`.zenodo.json`), contributing and changelog files added.

## 0.1.0 — 2026-11-04

- First public snapshot of the pipeline (WCVP + ENA, MAFFT, p-distance, NJ) and the Turkish-language website.
