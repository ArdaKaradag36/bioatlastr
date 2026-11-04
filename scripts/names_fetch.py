"""TASK 2 fetchers (cached, resumable, polite). Usage: names_fetch.py wikidata|gbif|inat
Reads runs/full/data/{species,synonyms}.csv (read-only); writes only data/names/cache/*."""
import hashlib, json, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd, requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "names" / "cache"
UA = {"User-Agent": "bio-web-turkish-names/0.1 (student research project; open-source; low rate)"}
sp = pd.read_csv(ROOT / "runs/full/data/species.csv", keep_default_na=False)
syn = pd.read_csv(ROOT / "runs/full/data/synonyms.csv", keep_default_na=False)
SPECIES = list(sp["species"]); GENERA = sorted(set(sp["genus"])); FAMILIES = sorted(set(sp["family"]))

def cached_get(sub: str, key: str, url: str, params=None, sleep=0.0, tries=6, timeout=90, post=False):
    f = CACHE / sub / (hashlib.md5(key.encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    f.parent.mkdir(parents=True, exist_ok=True)
    for a in range(tries):
        try:
            r = (requests.post(url, data=params, headers=UA, timeout=timeout) if post else requests.get(url, params=params, headers=UA, timeout=timeout))
            if r.status_code in (429, 500, 502, 503, 504):
                wait = min(120, 5 * 2 ** a); print(f"  ! {sub} HTTP {r.status_code}, retry in {wait}s", flush=True); time.sleep(wait); continue
            if r.status_code >= 400: print(f"  ! {sub} HTTP {r.status_code}: {r.text[:120]!r}", flush=True)
            r.raise_for_status()
            data = r.json(); f.write_text(json.dumps(data)); time.sleep(sleep); return data
        except (requests.RequestException, ValueError) as e:
            wait = min(120, 5 * 2 ** a); print(f"  ! {sub} {type(e).__name__}, retry in {wait}s", flush=True); time.sleep(wait)
    return None

# ---------------------------------------------------------------- Wikidata (CC0)
Q_COMMON = '''SELECT ?name ?item ?rank ?cn ?inat ?gb WHERE { VALUES ?name { %s } ?item wdt:P225 ?name; wdt:P105 ?rank.
 VALUES ?rank { wd:Q7432 wd:Q34740 wd:Q35409 }
 OPTIONAL { ?item wdt:P1843 ?cn FILTER(LANG(?cn)="tr") } OPTIONAL { ?item wdt:P3151 ?inat } OPTIONAL { ?item wdt:P846 ?gb } }'''
Q_LABELS = '''SELECT ?name ?item ?lab ?al ?wt ?par WHERE { VALUES ?name { %s } ?item wdt:P225 ?name; wdt:P105 ?rank.
 VALUES ?rank { wd:Q7432 wd:Q34740 wd:Q35409 }
 OPTIONAL { ?item rdfs:label ?lab FILTER(LANG(?lab)="tr") } OPTIONAL { ?item skos:altLabel ?al FILTER(LANG(?al)="tr") }
 OPTIONAL { ?w schema:about ?item; schema:isPartOf <https://tr.wikipedia.org/>; schema:name ?wt }
 OPTIONAL { ?item wdt:P171 ?p. ?p wdt:P225 ?par } }'''

def wikidata():
    syn_names = sorted(set(syn.loc[syn.accepted.isin(SPECIES), "synonym"]))
    names = SPECIES + GENERA + FAMILIES + syn_names
    batches = [names[i:i + 250] for i in range(0, len(names), 250)]
    print(f"[wikidata] {len(names)} names, {len(batches)} batches", flush=True)
    t0 = time.time(); fails = 0
    for i, b in enumerate(batches, 1):
        vals = " ".join('"%s"' % n.replace('"', "") for n in b)
        for tag, q in (("common", Q_COMMON), ("labels", Q_LABELS)):
            d = cached_get("wikidata", tag + vals, "https://query.wikidata.org/sparql", {"query": q % vals, "format": "json"}, sleep=1.0, timeout=100, post=True)
            fails += d is None
        if i % 10 == 0 or i == len(batches):
            print(f"  [{time.strftime('%H:%M:%S')}] wikidata batch {i}/{len(batches)} ({time.time()-t0:.0f}s) failures {fails}", flush=True)
    print("WIKIDATA_DONE", flush=True)

# ---------------------------------------------------------------- GBIF (vernacular names; per-record source)
def gbif():
    todo = [(n, "species") for n in SPECIES] + [(n, "genus") for n in GENERA] + [(n, "family") for n in FAMILIES]
    done = [0]; lock = threading.Lock(); t0 = time.time()
    def work(item):
        name, rank = item
        m = cached_get("gbif_match", f"{rank}:{name}", "https://api.gbif.org/v1/species/match", {"name": name, "rank": rank, "kingdom": "Plantae", "strict": "true"})
        key = (m or {}).get("acceptedUsageKey") or (m or {}).get("usageKey")
        v = None
        if key and (m or {}).get("matchType") in ("EXACT", "HIGHERRANK") and (m.get("rank") or "").lower() == rank:
            v = cached_get("gbif_vern", str(key), f"https://api.gbif.org/v1/species/{key}/vernacularNames", {"limit": 500})
        with lock:
            done[0] += 1
            if done[0] % 500 == 0:
                print(f"  [{time.strftime('%H:%M:%S')}] gbif {done[0]}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(work, todo))
    print("GBIF_DONE", flush=True)

# ---------------------------------------------------------------- iNaturalist (ids from Wikidata P3151, 30 per call, ~1 call/s)
def inat():
    ids = set()
    for f in (CACHE / "wikidata").glob("*.json"):
        d = json.loads(f.read_text())
        for b in d["results"]["bindings"]:
            if "inat" in b: ids.add(int(b["inat"]["value"]))
    ids = sorted(ids); batches = [ids[i:i + 30] for i in range(0, len(ids), 30)]
    print(f"[inat] {len(ids)} taxon ids, {len(batches)} calls", flush=True); t0 = time.time()
    for i, b in enumerate(batches, 1):
        cached_get("inat", ",".join(map(str, b)), "https://api.inaturalist.org/v1/taxa/" + ",".join(map(str, b)),
                   {"locale": "tr", "all_names": "true", "per_page": 30}, sleep=1.1)
        if i % 20 == 0 or i == len(batches):
            print(f"  [{time.strftime('%H:%M:%S')}] inat {i}/{len(batches)} ({time.time()-t0:.0f}s)", flush=True)
    print("INAT_DONE", flush=True)

if __name__ == "__main__":
    {"wikidata": wikidata, "gbif": gbif, "inat": inat}[sys.argv[1]]()
