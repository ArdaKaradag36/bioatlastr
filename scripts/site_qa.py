"""Visual + a11y QA of the built site (npx next start -p 3200).
Usage: pipeline/.venv/bin/python scripts/site_qa.py [shots]   -> screenshots in docs/screenshots/, axe summary on stdout."""
import json, sys
from playwright.sync_api import sync_playwright
B = "http://localhost:3200"
PAGES = {"anasayfa": "/", "turler": "/turler", "tur": "/turler/quercus-aucheri", "tur-bos": "/turler/atriplex-sukhorukovii",
         "agaclar": "/agaclar?aile=Cyperaceae&marker=rbcL&grup=Cyperaceae/Carex", "veri-bosluklari": "/veri-bosluklari",
         "dizi-ara": "/dizi-ara", "sozluk": "/sozluk", "yontem": "/yontem", "kaynaklar": "/kaynaklar"}
AXE = open("web/node_modules/axe-core/axe.min.js").read()
shots = len(sys.argv) > 1
errors, overflow, viol = [], [], {}
with sync_playwright() as p:
    br = p.chromium.launch()
    for scheme in ("light", "dark"):
        for vname, vp in (("mobil", {"width": 390, "height": 800}), ("masaustu", {"width": 1280, "height": 900})):
            ctx = br.new_context(viewport=vp, color_scheme=scheme, has_touch=(vname == "mobil"))
            pg = ctx.new_page()
            pg.on("console", lambda m: errors.append((pg.url, m.text[:160])) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append((pg.url, str(e)[:160])))
            for name, path in PAGES.items():
                pg.goto(B + path, wait_until="networkidle"); pg.wait_for_timeout(1500 if name == "agaclar" else 300)
                ow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                if ow > 0: overflow.append((scheme, vname, name, ow))
                if shots and (scheme == "light" or name in ("anasayfa", "tur")):
                    pg.screenshot(path=f"docs/screenshots/{name}-{vname}{'-koyu' if scheme == 'dark' else ''}.png", full_page=(name != "agaclar"))
                pg.evaluate(AXE)
                r = pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,ex:v.nodes.slice(0,2).map(n=>n.target.join(' ')+' | '+(n.any[0]?.message||n.all[0]?.message||'').slice(0,110))})))")
                for v in r: viol.setdefault((scheme, vname, name), []).append(v)
            ctx.close()
    br.close()
print("CONSOLE ERRORS:", errors[:10]); print("OVERFLOW:", overflow)
tot = 0
for k, vs in viol.items():
    for v in vs:
        tot += v["n"]; print(k, v["id"], v["impact"], v["n"], v["ex"])
print("TOTAL axe violating nodes:", tot, "pages-checked:", 4 * len(PAGES))
