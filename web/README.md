# Türkiye Bitki DNA Barkod Atlası — web

Static Next.js (App Router) site for the Turkey Plant DNA Barcode Atlas. Data under `public/data/` is produced by the Python pipeline; the site does not call ENA/NCBI at runtime.

## Commands

```bash
npm ci
npm test          # unit tests (tsx)
npm run build     # static export → out/
npm start         # serve the production build
npm run test:e2e  # Playwright (+ axe on Chromium); starts the server itself
```

Root Directory for hosting is `web/`. GitHub Pages builds from `main` via `.github/workflows/pages.yml` (`push` to `main` or `workflow_dispatch`).

## Accessibility

See `../docs/accessibility.md` for the latest local Playwright + axe run.
