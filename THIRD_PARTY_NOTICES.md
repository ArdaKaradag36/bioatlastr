# Third-party notices

## Data sources (details and evidence: `docs/licence_audit.md`, `data/names/LICENSES.md`)
- **WCVP** - World Checklist of Vascular Plants, Royal Botanic Gardens, Kew. CC BY 3.0. Govaerts R. (ed.) 2026, https://doi.org/10.34885/egs6-cp24.
- **ENA / INSDC** - sequence records; INSDC policy: free and unrestricted access, no use restrictions. Credit the original submission (accession).
- **Wikidata** - CC0 1.0. **Vikipedi (tr.wikipedia.org)** - article titles, CC BY-SA (Wikimedia Terms of Use).
- **Catalogue of Life** - CC BY 4.0, Bánki O. et al. (2026), https://doi.org/10.48580/dgyy9 (via GBIF).
- **Cichorieae Systematics Portal** - CC BY 4.0, Kilian N. (2024), https://doi.org/10.15468/gzcrwf (via GBIF).
- **GBIF** (api.gbif.org) is used only as an access route; each dataset's own licence applies.

## Software dependencies (checked 2026-11-04 from installed package metadata)
Web (npm, `web/package-lock.json`): about 400 packages, almost all MIT / ISC / Apache-2.0 / BSD / 0BSD / BlueOak / CC-BY-4.0 (caniuse-lite, build-time only) / Python-2.0 (argparse, dev-time).
Direct runtime dependencies: next, react, react-dom (MIT), d3-selection, d3-zoom (ISC), server-only (MIT).
Non-permissive or weak-copyleft entries (all transitive, build-time, not copied into this repository or the site output):
- `@img/sharp-libvips-*`, `@img/sharp-wasm32` - LGPL-3.0-or-later; optional image-optimisation binaries pulled by Next.js. The site uses no images, so they are unused.
- `lightningcss*`, `axe-core`, `@vercel/og` - MPL-2.0 (file-level copyleft; unmodified, build/dev tools).

Python (pipeline, `pipeline/requirements.txt`): biopython (Biopython License / BSD-3-Clause), requests (Apache-2.0), pandas, numpy (BSD-3), PyYAML (MIT),
matplotlib (PSF-style), pytest (MIT); transitive `certifi` is MPL-2.0 (unmodified). No GPL or AGPL packages were found.
External tool: MAFFT (BSD-style licence, not distributed here; install separately).

## Fonts, icons, images
The site loads no web fonts and ships no images, icons or photographs other than a plain generated `favicon.ico` (a green circle drawn for this project). All text is original.
