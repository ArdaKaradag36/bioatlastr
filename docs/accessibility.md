# Accessibility check (Playwright + axe)

**Date:** 2026-11-10  
**Environment:** local `npm run build` then Playwright `webServer` (`npm run start -- --port 3210`), Chromium, viewport 390×800  
**Command:** `npx playwright test e2e/mobile.spec.ts --project=chromium -g "axe"`

## Pages

| Path | serious/critical axe violations |
|---|---:|
| `/` | 0 |
| `/turler` | 0 |
| `/turler/acanthus-mollis` | 0 |
| `/agaclar` | 0 |
| `/dizi-ara` | 0 |
| `/en` | 0 |
| `/veri-bosluklari` | 0 |

**Result:** test passed — no serious or critical axe violations on the pages above. Moderate/minor findings were not asserted by the suite.
