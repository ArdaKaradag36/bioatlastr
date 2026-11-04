"""Browser check of the built site (npx next start -p 3200). Usage: pipeline/.venv/bin/python scripts/site_check.py"""
import re, sys, time
from playwright.sync_api import sync_playwright
B = "http://localhost:3200"
fa = open("runs/full/data/sequences/rbcL.fasta").read().split(">")[1:]
q = [x for x in fa if " Quercus aucheri" in x.split("\n")[0] or " Quercus ilex" in x.split("\n")[0]][0]
qname = q.split("\n")[0].split(" ", 1)[1]; qseq = "".join(q.split("\n")[1:])
errors = []
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1280, "height": 900})
    pg.on("console", lambda m: errors.append((pg.url, m.text[:150])) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append((pg.url, str(e)[:150])))
    def visit(path, wait="networkidle"):
        t = time.time(); pg.goto(B + path, wait_until=wait); dt = time.time() - t
        return dt
    def text(): return re.sub(r"\s+", " ", pg.inner_text("body"))
    dt = visit("/"); t = text()
    print("HOME", f"{dt:.2f}s", [x in t for x in ("10.007", "4.088", "3.003", "5.919")])
    # search autocomplete on /turler
    visit("/turler"); inp = pg.locator('input[role=combobox],input[type=search]').first
    inp.fill("quercus auch"); pg.wait_for_timeout(800)
    print("SEARCH latin:", [x.inner_text()[:40] for x in pg.locator('[role=option]').all()[:3]])
    inp.fill("quercus iilex"); pg.wait_for_timeout(800)
    print("SEARCH fuzzy:", [x.inner_text()[:40] for x in pg.locator('[role=option]').all()[:3]])
    pg.screenshot(path="/tmp/shots/search.png")
    for slug in ("quercus-aucheri", "atriplex-sukhorukovii"):
        dt = visit(f"/turler/{slug}"); pg.wait_for_timeout(1200); t = text()
        print("SPECIES", slug, f"{dt:.2f}s", len(t), "|", t[150:700])
        pg.screenshot(path=f"/tmp/shots/{slug}.png", full_page=True)
    dt = visit("/agaclar?aile=Cyperaceae&marker=rbcL&grup=Cyperaceae/Carex"); pg.wait_for_timeout(2500)
    n = pg.locator("svg.touch-none text").count(); c = pg.locator("svg.touch-none circle, svg.touch-none path, svg.touch-none line").count()
    print("TREE Carex rbcL", f"{dt:.2f}s", "svg text labels:", n, "shapes:", c)
    svg = pg.locator("svg.touch-none").first; box = svg.bounding_box()
    pg.mouse.move(box["x"] + 300, box["y"] + 200); pg.mouse.wheel(0, -600); pg.wait_for_timeout(500)
    pg.mouse.down(); pg.mouse.move(box["x"] + 200, box["y"] + 150); pg.mouse.up()
    pg.screenshot(path="/tmp/shots/tree.png")
    dt = visit("/veri-bosluklari"); pg.wait_for_timeout(800); t = text()
    print("GAPS", f"{dt:.2f}s", "3.003" in t, t[150:450])
    dt = visit("/dizi-ara")
    pg.fill("textarea", qseq); pg.select_option("select", "rbcL"); pg.get_by_role("button", name="Karşılaştır").click(); pg.wait_for_timeout(3000)
    t = text(); print("SEQSEARCH query was", qname, "|", t[t.find("Karşılaştır"):][:600])
    pg.screenshot(path="/tmp/shots/seqsearch.png", full_page=True)
    dt = visit("/yontem"); print("YONTEM", f"{dt:.2f}s", len(text()))
    open("/tmp/yontem.txt", "w").write(text())
    br.close()
print("CONSOLE ERRORS:", errors[:8] or "none")
