"""Phase 2 (default): barcode sequences from ENA (European Nucleotide Archive).

ENA mirrors GenBank/DDBJ (INSDC), needs no account and no key.
Steps
  1. every genus of the species list -> ENA tax_id (taxonomy REST)
  2. per genus and marker: Portal API search  tax_tree(<id>) AND <marker words> AND length limits
  3. client-side marker/name filters (accepted WCVP names + synonyms), aggregated logs
  4. FASTA of the candidates in batches (Browser API)
  5. sequence quality filters, near-duplicate limit, cap per species and marker
Everything is cached on disk (data/cache/ena), so an interrupted run resumes where it stopped.
"""

from __future__ import annotations

import csv
import json
import re
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Callable

import pandas as pd
import requests

from .filters import check_sequence, clean_sequence, n_fraction
from .http_cache import DiskCache, cache_key
from .names import build_name_index, match_record
from .ncbi import write_outputs
from .paths import DATA, SPECIES_CSV, SYNONYMS_CSV

PORTAL = "https://www.ebi.ac.uk/ena/portal/api"
BROWSER = "https://www.ebi.ac.uk/ena/browser/api"
TAXONOMY = "https://www.ebi.ac.uk/ena/taxonomy/rest/scientific-name/"

SEARCH_FIELDS = "accession,description,scientific_name,tax_id,base_count,country,mol_type,organelle,specimen_voucher,first_public"
FILTER_SUMMARY_CSV = DATA / "ena_filter_summary.csv"
UNMATCHED_CSV = DATA / "unmatched_names.csv"
RETRIEVAL_JSON = DATA / "sequence_source.json"

TURKEY_RE = re.compile(r"^(turkey|türkiye|turkiye)\b", re.I)


def is_turkey(country: str | None) -> bool:
    return bool(country and TURKEY_RE.match(country.strip()))


class RateLimiter:
    """Thread-safe: at most `rate` requests per second over all threads."""

    def __init__(self, rate: float):
        self.interval = 1.0 / rate
        self._next = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self.interval
        if start > now:
            time.sleep(start - now)


class EnaClient:
    """GET with disk cache, rate limit (<= max_requests_per_second) and exponential back-off."""

    def __init__(self, ena_cfg: dict[str, Any], session: requests.Session | None = None,
                 sleep: Callable[[float], None] = time.sleep):
        self.limiter = RateLimiter(float(ena_cfg["max_requests_per_second"]))
        self.max_retries = int(ena_cfg["max_retries"])
        self.cache = DiskCache("ena")
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "turkey-plant-barcode-atlas/0.2 (research project; github.com/ArdaKaradag36/bioatlastr)"})
        self._sleep = sleep
        self.network_calls = 0
        self.cache_hits = 0

    def get_text(self, url: str, params: dict[str, Any] | None = None, timeout: int = 180) -> str:
        key = cache_key(url, params or {})
        hit = self.cache.get(key)
        if hit is not None:
            self.cache_hits += 1
            return hit["t"]
        last: Exception | None = None
        for attempt in range(self.max_retries):
            self.limiter.wait()
            self.network_calls += 1
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
                if resp.status_code == 200:
                    self.cache.set(key, {"t": resp.text})
                    return resp.text
                if resp.status_code == 404:
                    self.cache.set(key, {"t": ""})
                    return ""
                last = RuntimeError(f"HTTP {resp.status_code}")
            except requests.RequestException as exc:
                last = exc
            wait = min(60, 2 ** (attempt + 1))  # 2, 4, 8 ... 60 s
            print(f"  ! ENA {last} (attempt {attempt + 1}/{self.max_retries}); retry in {wait}s", flush=True)
            self._sleep(wait)
        raise RuntimeError(f"ENA: giving up after {self.max_retries} attempts ({last}) for {url} {params or ''}")


# ----------------------------------------------------------------- taxonomy
ANY_NAME = "https://www.ebi.ac.uk/ena/taxonomy/rest/any-name/"


def _parse_entries(text: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(text) if text.strip() else []
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def resolve_genus(client: EnaClient, genus: str) -> tuple[int | None, str, str]:
    """Genus name -> (ENA tax_id, ENA genus name, method).

    method: 'scientific-name' (exact), 'any-name' (WCVP name is a synonym in NCBI/ENA taxonomy, e.g.
    Acinos -> Clinopodium, Amygdalus -> Prunus; sequences are filed under the NCBI name), or 'none'.
    """
    entries = _parse_entries(client.get_text(TAXONOMY + requests.utils.quote(genus)))
    tid = pick_genus_entry(entries, genus)
    if tid is not None:
        return tid, genus, "scientific-name"
    for e in _parse_entries(client.get_text(ANY_NAME + requests.utils.quote(genus))):
        if e.get("rank") == "genus" and "Viridiplantae" in e.get("lineage", ""):
            return int(e["taxId"]), e["scientificName"], "any-name"
    return None, "", "none"


def pick_genus_entry(entries: list[dict[str, Any]], genus: str) -> int | None:
    """Choose the plant (Viridiplantae) entry of rank genus; homonyms in animals/fungi are ignored."""
    for e in entries:
        if e.get("scientificName") == genus and e.get("rank") == "genus" and "Viridiplantae" in e.get("lineage", ""):
            return int(e["taxId"])
    return None


# ------------------------------------------------------------------- search
def build_query(tax_id: int, markers_cfg: dict[str, Any] | list[dict[str, Any]], extra: str = "") -> str:
    """One query per genus for all markers: union of the marker words, widest length window."""
    mlist = [markers_cfg] if "ena_terms" in markers_cfg else list(markers_cfg.values())
    terms: list[str] = []
    for m in mlist:
        terms += [t for t in m["ena_terms"] if t not in terms]
    where = " OR ".join(f'description="*{t}*"' for t in terms)
    q = (f"tax_tree({tax_id}) AND ({where}) AND base_count>={min(int(m['min_length']) for m in mlist)} "
         f"AND base_count<={max(int(m['max_length']) for m in mlist)}")
    return f"{q} AND {extra}" if extra else q


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def classify_record(description: str, length: int, markers: dict[str, Any]) -> tuple[str | None, str | None]:
    """(marker, None) when the record is a clean barcode record, else (marker or None, reason)."""
    description = description or ""
    if not description.strip():
        return None, "missing_description"
    hits = [m for m, mc in markers.items() if not marker_reason_include(description, mc)]
    if not hits:
        return None, "marker_not_in_description"
    if len(hits) > 1:
        return None, "multi_marker_record"
    m = hits[0]
    mc = markers[m]
    why = marker_reason(description, mc)
    if why:
        return m, why
    if length < mc["min_length"]:
        return m, "too_short"
    if length > mc["max_length"]:
        return m, "too_long"
    return m, None


def parse_tsv(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    rows = []
    for row in csv.DictReader(text.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE):
        row.pop(None, None)  # surplus fields of a malformed line
        rows.append({k: ("" if v is None else v) for k, v in row.items()})  # short lines give None -> ""
    return rows


def search_records(client: EnaClient, query: str, page_size: int, years: tuple[int, int] = (1970, date.today().year + 1)) -> list[dict[str, str]]:
    """All records of a query. ENA has no offset: results above `page_size` are re-fetched in year windows."""
    text = client.get_text(f"{PORTAL}/search", {"result": "sequence", "query": query,
                                                "fields": SEARCH_FIELDS, "format": "tsv", "limit": 0})
    rows = parse_tsv(text)
    y0, y1 = years
    if len(rows) <= page_size or y0 >= y1:
        return rows
    mid = (y0 + y1) // 2
    out: list[dict[str, str]] = []
    for a, b in ((y0, mid), (mid + 1, y1)):
        window = f"first_public>={a}-01-01 AND first_public<={b}-12-31"
        out += search_records(client, f"{query} AND {window}", page_size, (a, b))
    return out


def marker_reason_include(description: str | None, marker_cfg: dict[str, Any]) -> str | None:
    description = description or ""
    inc = marker_cfg.get("ena_include_regex")
    if inc and not re.search(inc, description):
        return "marker_not_in_description"
    return None


def marker_reason(description: str, marker_cfg: dict[str, Any]) -> str | None:
    """Keep only records whose description really is the marker (not a spacer, genome or pseudogene)."""
    description = description or ""
    if marker_reason_include(description, marker_cfg):
        return "marker_not_in_description"
    exc = marker_cfg.get("ena_exclude_regex")
    if exc and re.search(exc, description, re.I):
        return "wrong_region_or_genome"
    return None


def parse_fasta(text: str) -> dict[str, str]:
    """ENA FASTA ('>ENA|AB125020|AB125020.1 name') -> {accession: sequence}."""
    out: dict[str, list[str]] = {}
    acc = None
    for line in text.splitlines():
        if line.startswith(">"):
            parts = line[1:].split()[0].split("|")
            acc = parts[1] if len(parts) >= 2 else parts[0]
            out[acc] = []
        elif acc is not None:
            out[acc].append(line.strip())
    return {a: "".join(v) for a, v in out.items()}


# ----------------------------------------------------------- selection logic
def select_sequences(records: list[dict[str, Any]], cap: int, max_identical: int) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Pick at most `cap` sequences for one species + marker.

    Order of preference: sequences from Turkey, distinct sequences before repeated identical
    ones (at most `max_identical` copies of one exact sequence are ever kept), longer first.
    Returns (kept, [(dropped record, reason)]).
    """
    dropped: list[tuple[dict, str]] = []
    seen: Counter = Counter()
    ranked: list[tuple[tuple, dict]] = []
    for r in sorted(records, key=lambda r: (not r["is_turkey"], -r["length"], r["accession"])):
        seen[r["sequence"]] += 1
        if seen[r["sequence"]] > max_identical:
            dropped.append((r, "near_duplicate"))
            continue
        ranked.append(((seen[r["sequence"]] > 1, not r["is_turkey"], -r["length"], r["accession"]), r))
    ranked.sort(key=lambda x: x[0])
    kept = [r for _, r in ranked[:cap]]
    dropped += [(r, "not_selected_cap") for _, r in ranked[cap:]]
    return kept, dropped


# ---------------------------------------------------------------- the phase
def read_synonyms() -> list[tuple[str, str]]:
    if not SYNONYMS_CSV.exists():
        return []
    df = pd.read_csv(SYNONYMS_CSV, keep_default_na=False)
    return list(zip(df["synonym"], df["accepted"]))


def run_phase2_ena(cfg: dict[str, Any]) -> None:
    ena_cfg = cfg["ena"]
    markers: dict[str, Any] = cfg["markers"]
    client = EnaClient(ena_cfg)
    species_df = pd.read_csv(SPECIES_CSV, keep_default_na=False)
    info = {r["species"]: r for _, r in species_df.iterrows()}
    synonyms = read_synonyms()
    index = build_name_index(info.keys(), synonyms)
    n_syn = sum(1 for v in index.values() if v[1] == "synonym")
    print(f"[phase 2/ENA] {len(info)} species, {n_syn} usable WCVP synonyms", flush=True)

    # 1) genera to query: accepted genera + genera of synonyms
    genera = sorted({s.split()[0] for s in index})
    accepted_genera = {i["genus"] for i in info.values()}
    t0 = time.time()
    with ThreadPoolExecutor(int(ena_cfg["workers"])) as ex:
        resolved = dict(zip(genera, ex.map(lambda g: resolve_genus(client, g), genera)))
    tax_ids = {g: r[0] for g, r in resolved.items()}
    unresolved = [g for g, t in tax_ids.items() if t is None]
    with open(DATA / "ena_genus_resolution.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["wcvp_genus", "wcvp_accepted_genus", "ena_tax_id", "ena_genus", "method"])
        for g in genera:
            w.writerow([g, int(g in accepted_genera), resolved[g][0] or "", resolved[g][1], resolved[g][2]])
    by_method = Counter(r[2] for r in resolved.values())
    missing_acc = sorted(g for g in unresolved if g in accepted_genera)
    print(f"[phase 2/ENA] genera: {len(genera)} ({len(accepted_genera)} accepted + {len(genera) - len(accepted_genera)} synonym-only); "
          f"resolution {dict(by_method)}; no ENA taxon: {len(unresolved)} (accepted genera among them: {len(missing_acc)})"
          f" ({time.time() - t0:.0f}s)", flush=True)

    # WCVP genus names that ENA files under another genus (any-name resolution): ENA genus -> WCVP genera
    genus_alias: dict[str, list[str]] = defaultdict(list)
    for g, (_, ena_name, method) in resolved.items():
        if method == "any-name" and ena_name != g:
            genus_alias[ena_name].append(g)

    # 2) search per ENA taxon (several WCVP names can point to the same ENA genus)
    jobs = sorted({t for t in tax_ids.values() if t})
    taxon_of = {t: g for g, t in tax_ids.items() if t}
    raw_rows: dict[str, dict[str, str]] = {}
    failures: list[tuple[str, str, str]] = []
    done = 0

    def work(tid: int):
        g = taxon_of[tid]
        try:
            return g, search_records(client, build_query(tid, markers), ena_cfg["page_size"]), None
        except Exception as exc:  # network problems: log, continue, resume on next run
            return g, [], str(exc)

    with ThreadPoolExecutor(int(ena_cfg["workers"])) as ex:
        for fut in as_completed([ex.submit(work, t) for t in jobs]):
            g, rows, err = fut.result()
            done += 1
            if err:
                failures.append((g, "all", err))
            for r in rows:
                raw_rows[r["accession"]] = r
            if done % 100 == 0:
                print(f"  [{time.strftime('%H:%M:%S')}] searched {done}/{len(jobs)} genera ({time.time() - t0:.0f}s); "
                      f"records so far {len(raw_rows)}, failed searches {len(failures)}, network calls {client.network_calls} "
                      "(results are cached on disk = checkpoint; re-run resumes)", flush=True)
    if failures:
        print(f"[phase 2/ENA] WARNING: {len(failures)} searches failed (ENA unavailable?); re-run to resume. First: {failures[0]}")

    # 3) metadata filters + name matching (counts only; per-record log for later stages)
    summary: Counter = Counter()
    unmatched: dict[str, Counter] = defaultdict(Counter)
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for acc, r in raw_rows.items():
        desc = r.get("description") or ""
        m, why = classify_record(desc, _to_int(r.get("base_count")), markers)
        summary[(m or "unassigned", "raw_records")] += 1
        if why:
            summary[(m or "unassigned", f"dropped:{why}")] += 1
            continue
        sp, via, why = match_record(r.get("scientific_name") or "", desc, index, genus_alias)
        if why:
            summary[(m, f"dropped:{why}")] += 1
            if why == "unmatched_name":
                unmatched[r.get("scientific_name") or ""][m] += 1
            continue
        summary[(m, "name_matched")] += 1
        candidates[(sp, m)].append({
            "species": sp, "marker": m, "accession": acc, "definition": desc,
            "organism": r.get("scientific_name") or "", "country": r.get("country") or "",
            "voucher": r.get("specimen_voucher") or "", "length": _to_int(r.get("base_count")),
            "is_turkey": is_turkey(r.get("country")), "matched_via": via,
            "first_public": r.get("first_public") or "",
        })

    # limit candidates before downloading (Turkish first, then longest)
    max_c = int(ena_cfg["max_candidates_per_species_marker"])
    to_fetch: set[str] = set()
    for key, recs in candidates.items():
        recs.sort(key=lambda r: (not r["is_turkey"], -r["length"], r["accession"]))
        for r in recs[:max_c]:
            to_fetch.add(r["accession"])
        for r in recs[max_c:]:
            summary[(key[1], "dropped:not_downloaded_candidate_cap")] += 1
    print(f"[phase 2/ENA] records without description: {summary[('unassigned', 'dropped:missing_description')]} "
          f"of {len(raw_rows)} (dropped, reason 'missing_description')", flush=True)
    print(f"[phase 2/ENA] name-matched candidates: {sum(len(v) for v in candidates.values())}, "
          f"to download: {len(to_fetch)}", flush=True)

    # 4) FASTA
    accs = sorted(to_fetch)
    bs = int(ena_cfg["fasta_batch"])
    batches = [accs[i:i + bs] for i in range(0, len(accs), bs)]
    seqs: dict[str, str] = {}

    def fetch(batch: list[str]):
        try:
            return parse_fasta(client.get_text(f"{BROWSER}/fasta/{','.join(batch)}", timeout=300)), None
        except Exception as exc:
            return {}, str(exc)

    fetch_errors = 0
    with ThreadPoolExecutor(int(ena_cfg["workers"])) as ex:
        for i, fut in enumerate(as_completed([ex.submit(fetch, b) for b in batches]), 1):
            got, err = fut.result()
            seqs.update(got)
            fetch_errors += bool(err)
            if i % 50 == 0:
                print(f"  FASTA batches {i}/{len(batches)}", flush=True)
    if fetch_errors:
        print(f"[phase 2/ENA] WARNING: {fetch_errors} FASTA batches failed; re-run to resume.")

    # 5) sequence filters, duplicates, cap
    cap = int(cfg["max_per_species_marker"])
    max_ident = int(ena_cfg["max_identical_copies"])
    table: list[dict[str, Any]] = []
    fasta: dict[str, list[tuple[str, str]]] = {m: [] for m in markers}
    dropped_log: list[dict[str, Any]] = []
    for (sp, m), recs in sorted(candidates.items()):
        mc = markers[m]
        good: list[dict[str, Any]] = []
        for r in sorted(recs, key=lambda r: (not r["is_turkey"], -r["length"], r["accession"]))[:max_c]:
            raw = seqs.get(r["accession"])
            if raw is None:
                summary[(m, "dropped:fasta_missing")] += 1
                continue
            seq = clean_sequence(raw)
            why = check_sequence(seq, mc["min_length"], mc["max_n_fraction"])
            if not why and len(seq) > mc["max_length"]:
                why = "too_long"
            if why:
                summary[(m, f"dropped:{why}")] += 1
                dropped_log.append({"species": sp, "marker": m, "accession": r["accession"], "stage": "sequence",
                                    "reason": why, "detail": f"length={len(seq)}"})
                continue
            r = {**r, "sequence": seq, "length": len(seq), "n_fraction": round(n_fraction(seq), 5)}
            good.append(r)
        kept, dropped = select_sequences(good, cap, max_ident)
        for r, why in dropped:
            summary[(m, f"dropped:{why}")] += 1
            dropped_log.append({"species": sp, "marker": m, "accession": r["accession"], "stage": "selection",
                                "reason": why, "detail": f"cap={cap}"})
        for r in kept:
            summary[(m, "kept")] += 1
            summary[(m, "kept_from_turkey")] += int(r["is_turkey"])
            table.append({
                "species": sp, "family": info[sp]["family"], "genus": info[sp]["genus"], "marker": m,
                "accession": r["accession"], "length": r["length"], "source_title": "",
                "definition": r["definition"], "organism": r["organism"], "n_fraction": r["n_fraction"],
                "country": r["country"], "voucher": r["voucher"], "is_turkey": int(r["is_turkey"]),
                "matched_via": r["matched_via"], "source": "ENA",
            })
            fasta[m].append((f"{r['accession']} {sp}", r["sequence"]))
    write_outputs(table, fasta, dropped_log)

    # logs: filter summary per marker, unmatched names, retrieval date
    with open(FILTER_SUMMARY_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["marker", "step", "count"])
        for (m, step), n in sorted(summary.items()):
            w.writerow([m, step, n])
    with open(UNMATCHED_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["scientific_name", "n_records", "markers"])
        for name, c in sorted(unmatched.items(), key=lambda kv: -sum(kv[1].values())):
            w.writerow([name, sum(c.values()), ";".join(sorted(c))])
    with open(RETRIEVAL_JSON, "w", encoding="utf-8") as fh:
        json.dump({"source": "ENA (INSDC mirror)", "retrieved": date.today().isoformat(),
                   "genera_queried": len(jobs), "genera_unresolved": unresolved,
                   "accepted_genera_without_ena_taxon": missing_acc,
                   "search_failures": len(failures), "fasta_failures": fetch_errors,
                   "records_kept": len(table), "network_calls": client.network_calls,
                   "cache_hits": client.cache_hits}, fh, ensure_ascii=False, indent=1)
    kept_by = Counter(r["marker"] for r in table)
    print(f"[phase 2/ENA] kept {len(table)} sequences {dict(kept_by)}; network calls {client.network_calls}", flush=True)
    if failures or fetch_errors:
        raise SystemExit("Phase 2 incomplete (ENA errors) - run the same command again to resume.")
