# Contributing

This atlas is maintained by **Arda Karadağ** (software, pipeline, website) and **Buse Menekşe** (biological content and checks).

## Report an error

Write to `karadagardaa@gmail.com` (software / records on the site) or `busemenekse@ogr.eskisehir.edu.tr` (biology). Include the species name or accession and what is wrong.

Do not send unpublished DNA sequences by e-mail. Deposit them in ENA, GenBank or DDBJ:

https://www.ebi.ac.uk/ena/browser/submit

The next WCVP/ENA refresh of this atlas can then pick the public record up.

## Code and data changes

- Do not invent Turkish common names. Names come only from the open-licence sources listed in `DATA_LICENSE.md`.
- Do not re-fetch the full ENA set unless you mean to. Analysis-only reruns use existing intermediates (`runs/full`).
- Site numbers must come from `stats.json` / generated JSON, not from typed constants.
- After a pipeline change run `pytest pipeline/tests`. After a site change run `npm test`, `npx tsc --noEmit`, `npx eslint src`, `npm run build` in `web/`.

## Pull requests

Keep changes small. One concern per commit when you can. Do not commit secrets, NCBI keys, or files under `data/raw/` / `data/cache/`.
