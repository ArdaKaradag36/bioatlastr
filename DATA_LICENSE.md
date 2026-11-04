# Data licence

This project is a non-commercial university student research project. The data tables in this repository are **derived** from the
upstream sources below. You may reuse them, including commercially, **provided you give attribution to the upstream sources and respect
the share-alike condition where it applies**. The data are provided "as is", for research purposes only: they are estimates, have not been
verified by an expert and must not be used for scientific, regulatory or commercial decisions.

| Our files | Derived from | Licence of our file | What you must do |
|---|---|---|---|
| `data/species.csv`, `data/synonyms.csv`, `exports/turkiye_taxa.csv`, `exports/families.csv`, `exports/genera.csv`, `data/species_meta.json` | WCVP (Kew), CC BY 3.0 | CC BY 4.0 (a later version of CC BY, allowed for adaptations) | Cite WCVP (see below) and this project |
| `data/sequence_table.csv`, `data/sequences/*.fasta`, `web/public/data/**` (sequence records) | ENA / INSDC (no use restrictions) | CC BY 4.0 for our selection/annotation; sequence records themselves are INSDC public data | Cite the original submission by accession number; cite ENA |
| `results/**`, `web/public/data/**` (coverage, distances, trees, discrimination) | our analysis of the two sources above | CC BY 4.0 | Cite this project, WCVP and ENA |
| `data/names/turkish_names.csv`, `exports/*turkish_names*.csv`, `exports/species_without_turkish_name.csv`, Turkish names in `web/public/data/**` | Wikidata (CC0), Vikipedi titles (CC BY-SA), Catalogue of Life (CC BY 4.0), Cichorieae Systematics Portal (CC BY 4.0) | **CC BY-SA 4.0** (share-alike, because Vikipedi titles are included) | Attribute each source (the `source` / `source_id_or_url` columns), keep CC BY-SA 4.0 on derivatives of this table |

Excluded on purpose (not in the repository): iNaturalist and IUCN Red List names (non-commercial terms), names from marine species registers
(WoRMS, WRiMS), DAISIE, a railway EIA dataset, GRIN Taxonomy (licence could not be verified on its own pages), Bizim Bitkiler / Türkiye Bitkileri Listesi (no data licence stated).

Personal data: voucher / collector strings, locality text and submitter details from sequence records are removed (`scripts/sanitize_public.py`).

Suggested citation: see `CITATION.cff` and the "Atıf ve lisans" section on the site page `/kaynaklar`. Upstream licence evidence: `docs/licence_audit.md`.
Contact / takedown: PLACEHOLDER_CONTACT_EMAIL
