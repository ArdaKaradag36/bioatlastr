# Licence audit (2026-11-04)

Each row was checked on the source's own page where it could be fetched. "Unverified" = the page could not be fetched (Cloudflare 403) or states no licence.

| Source | Licence found | Evidence (own page) | Status | Decision |
|---|---|---|---|---|
| WCVP (Kew) | CC BY 3.0, cite Govaerts R. (ed.) 2026, doi:10.34885/egs6-cp24 | `README_WCVP.xlsx` shipped with the Kew download (sftp.kew.org/pub/data-repositories/WCVP/, 2026-06-04) | verified | keep, attribution |
| POWO website terms | - | powo.science.kew.org returned 403 (Cloudflare) | unverified | only linked, no POWO content copied |
| ENA / INSDC sequences | free and unrestricted access, no licensing requirements; credit the original submission | ebi.ac.uk/ena/browser/about/policies and insdc.org policy page | verified | keep, cite accession |
| Wikidata | CC0 1.0 for main/property namespaces | wikidata.org/wiki/Wikidata:Licensing | verified | keep |
| Catalogue of Life | CC BY 4.0 | catalogueoflife.org footer ("Unless otherwise indicated ... CC BY 4.0"); GBIF dataset 7ddf754f licence CC BY 4.0 | verified | keep, attribution |
| Vikipedi (tr) titles | CC BY-SA (tr: 3.0 + GFDL page; Wikimedia Terms of Use: CC BY-SA 4.0) | tr.wikipedia.org Telif hakları page; foundation.wikimedia.org Terms of Use | verified | keep (short titles, with link); names table labelled CC BY-SA 4.0 |
| Cichorieae Systematics Portal | CC BY 4.0 ("Unless otherwise noted (see images)") | cichorieae.e-taxonomy.net/portal/ footer; GBIF dataset ded724e7 CC BY 4.0 | verified | keep, attribution |
| GRIN Taxonomy | CC0 only in the GBIF registry (dataset 66dd0960) | GRIN pages (npgsweb.ars-grin.gov) state no data licence | unverified | **exclude** (6 rows, no coverage loss) |
| GBIF terms | per-dataset CC0 / CC BY / CC BY-NC | gbif.org/terms returned 403; per-dataset licences read from api.gbif.org; Internet Archive snapshot of the terms agrees | partly verified | used only as access route, only datasets with verified CC BY/CC0 |
| iNaturalist, IUCN Red List (tier B) | non-commercial | - | known restricted | **exclude** (private local copy only) |
| WoRMS, WRiMS, DAISIE, railway EIA dataset (tier C) | unclear / not plant-name sources | - | unverified | **exclude** |
| Bizim Bitkiler / NGBB | no data licence stated | - | unverified | not used |
