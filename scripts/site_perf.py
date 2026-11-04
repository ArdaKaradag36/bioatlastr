"""Transfer size (gzip, as served by next start) and load time per page. Needs the site on :3200."""
import json, time
from playwright.sync_api import sync_playwright
sl = [s for s in json.load(open("web/public/data/species_index.json")) if s["genus"] == "Astragalus" and sum(s["counts"].values()) > 0][0]["slug"]
pages = ["/", "/turler", "/veri-bosluklari", "/agaclar?aile=Cyperaceae&marker=rbcL&grup=Cyperaceae/Carex", f"/turler/{sl}", "/dizi-ara", "/yontem"]
with sync_playwright() as p:
    br = p.chromium.launch()
    for path in pages:
        ctx = br.new_context(); pg = ctx.new_page(); sizes = []
        pg.on("response", lambda r: sizes.append((r.url.split(":3200")[-1][:55], len(r.body()) if r.ok else 0)))
        t = time.time(); pg.goto("http://localhost:3200" + path, wait_until="networkidle"); dt = time.time() - t
        raw = sum(s for _, s in sizes); big = max(sizes, key=lambda x: x[1])
        print(f"{path[:60]:60s} {dt:5.2f}s  decoded {raw/1e6:5.2f} MB  biggest {big[0]} {big[1]/1e6:.2f} MB")
        ctx.close()
