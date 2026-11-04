"""Phase 2: download barcode sequences from NCBI Nucleotide with Biopython Entrez.

Steps for every species + marker:
  1. esearch  -> list of record ids (UIDs)
  2. esummary -> organism, title, length (cheap, used to filter BEFORE downloading)
  3. efetch   -> full GenBank record of the records we keep

All three steps are cached on disk (per search / per UID / per accession).
"""

from __future__ import annotations

import csv
import json
import re
import time
from io import StringIO
from typing import Any, Callable, Iterable

from Bio import Entrez, SeqIO

from .filters import check_name, check_sequence, clean_sequence, n_fraction
from .http_cache import DiskCache, RateLimiter, cache_key
from .paths import DATA, DROPPED_CSV, SEQUENCE_TABLE_CSV, SEQUENCES_DIR, SPECIES_CSV

TABLE_COLUMNS = [
    "species", "family", "genus", "marker", "accession", "length",
    "source_title", "definition", "organism", "n_fraction", "country", "voucher",
    "is_turkey", "matched_via", "source",
]
DROPPED_COLUMNS = ["species", "marker", "accession", "stage", "reason", "detail"]


class NcbiClient:
    """Entrez calls with disk cache, rate limit (3/s, or 10/s with key) and retries."""

    def __init__(self, email: str, api_key: str | None, sleep: Callable[[float], None] = time.sleep):
        Entrez.email = email
        Entrez.tool = "turkey-plant-barcode-atlas"
        if api_key:
            Entrez.api_key = api_key
        # NCBI limit: 3 requests/s without key, 10/s with key. Stay a bit below.
        self.limiter = RateLimiter(0.11 if api_key else 0.36)
        self.search_cache = DiskCache("ncbi_esearch")
        self.summary_cache = DiskCache("ncbi_esummary")
        self.record_cache = DiskCache("ncbi_genbank")
        self._sleep = sleep
        self.network_calls = 0

    def _call(self, func: Callable[..., Any], **kwargs: Any) -> str:
        """Run one Entrez function, return its text, retry on temporary errors."""
        last: Exception | None = None
        for attempt in range(6):
            self.limiter.wait()
            self.network_calls += 1
            try:
                handle = func(**kwargs)
                text = handle.read()
                handle.close()
                if isinstance(text, bytes):
                    text = text.decode("utf-8")
                return text
            except Exception as exc:  # network errors, HTTP 429/5xx, NCBI "busy" replies
                last = exc
                wait = min(60, 2 ** (attempt + 1))
                print(f"  ! NCBI call failed ({exc}); retry {attempt + 1}/6 in {wait}s")
                self._sleep(wait)
        raise RuntimeError(f"NCBI request failed after retries: {last}")

    # ---- step 1: esearch -------------------------------------------------
    def search_ids(self, term: str, retmax: int) -> list[str]:
        key = cache_key(term, retmax)
        hit = self.search_cache.get(key)
        if hit is not None:
            return hit["ids"]
        text = self._call(Entrez.esearch, db="nuccore", term=term, retmax=retmax, retmode="json")
        result = json.loads(text)["esearchresult"]
        ids = result.get("idlist", [])
        self.search_cache.set(key, {"term": term, "count": result.get("count"), "ids": ids})
        return ids

    # ---- step 2: esummary ------------------------------------------------
    def summaries(self, uids: Iterable[str], batch_size: int) -> dict[str, dict[str, Any]]:
        """uid -> summary dict. Only UIDs missing in the cache are requested."""
        uids = list(dict.fromkeys(uids))
        out: dict[str, dict[str, Any]] = {}
        missing: list[str] = []
        for uid in uids:
            hit = self.summary_cache.get(uid)
            if hit is not None:
                out[uid] = hit
            else:
                missing.append(uid)
        for i in range(0, len(missing), batch_size):
            batch = missing[i : i + batch_size]
            text = self._call(Entrez.esummary, db="nuccore", id=",".join(batch), retmode="json")
            result = json.loads(text).get("result", {})
            for uid in batch:
                item = result.get(uid) or {"uid": uid, "_missing": True}
                self.summary_cache.set(uid, item)
                out[uid] = item
        return out

    # ---- step 3: efetch --------------------------------------------------
    def genbank_records(self, accessions: Iterable[str], batch_size: int) -> dict[str, str]:
        """accession.version -> raw GenBank flat-file text."""
        accessions = list(dict.fromkeys(accessions))
        out: dict[str, str] = {}
        missing: list[str] = []
        for acc in accessions:
            hit = self.record_cache.get(acc)
            if hit is not None:
                out[acc] = hit["text"]
            else:
                missing.append(acc)
        for i in range(0, len(missing), batch_size):
            batch = missing[i : i + batch_size]
            text = self._call(Entrez.efetch, db="nuccore", id=",".join(batch), rettype="gb", retmode="text")
            for acc, rec_text in split_genbank(text).items():
                self.record_cache.set(acc, {"text": rec_text})
                out[acc] = rec_text
            for acc in batch:  # remember records NCBI did not return so we do not ask again
                if acc not in out and not self.record_cache.has(acc):
                    self.record_cache.set(acc, {"text": ""})
                    out[acc] = ""
        return out


def split_genbank(text: str) -> dict[str, str]:
    """Split a multi-record GenBank flat file into {accession.version: record text}."""
    records: dict[str, str] = {}
    for chunk in re.split(r"^//\s*$", text, flags=re.MULTILINE):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        m = re.search(r"^VERSION\s+(\S+)", chunk, flags=re.MULTILINE)
        if m:
            records[m.group(1)] = chunk + "\n//\n"
    return records


def parse_genbank(text: str) -> dict[str, Any] | None:
    """Pull the fields we need out of one GenBank record."""
    if not text.strip():
        return None
    rec = SeqIO.read(StringIO(text), "genbank")
    ref_title = ""
    for ref in rec.annotations.get("references", []):
        title = (getattr(ref, "title", "") or "").strip()
        if title and title.lower() != "direct submission":
            ref_title = title
            break
    country = voucher = ""
    for feat in rec.features:
        if feat.type == "source":
            country = (feat.qualifiers.get("country") or [""])[0]
            voucher = (feat.qualifiers.get("specimen_voucher") or feat.qualifiers.get("isolate") or [""])[0]
            break
    return {
        "accession": rec.id,  # accession.version
        "sequence": clean_sequence(str(rec.seq)),
        "definition": rec.description,
        "organism": rec.annotations.get("organism", ""),
        "reference_title": ref_title,
        "country": country,
        "voucher": voucher,
    }


def read_species_table() -> list[dict[str, str]]:
    with open(SPECIES_CSV, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_term(species: str, marker_cfg: dict[str, Any]) -> str:
    """Entrez query: organism AND marker words AND length range."""
    return (
        f'"{species}"[Organism] AND {marker_cfg["query"]} AND '
        f'{marker_cfg["min_length"]}:{marker_cfg["max_length"]}[SLEN]'
    )


def run_phase2(cfg: dict[str, Any]) -> None:
    species_rows = read_species_table()
    if not species_rows:
        raise SystemExit("data/species.csv is empty - run phase 1 first.")
    ncbi_cfg = cfg["ncbi"]
    client = NcbiClient(ncbi_cfg["email"], ncbi_cfg.get("api_key"))
    markers: dict[str, Any] = cfg["markers"]
    cap = cfg["max_sequences_per_species_marker"]
    batch = ncbi_cfg["batch_size"]
    allow_mismatch = cfg["allow_name_mismatch"]

    # --- step 1: esearch for every species and marker --------------------
    hits: dict[tuple[str, str], list[str]] = {}
    total = len(species_rows) * len(markers)
    done = 0
    for marker, mcfg in markers.items():
        for row in species_rows:
            ids = client.search_ids(build_term(row["species"], mcfg), ncbi_cfg["search_retmax"])
            hits[(row["species"], marker)] = ids
            done += 1
            if done % 50 == 0 or done == total:
                print(f"[phase 2] esearch {done}/{total}", flush=True)

    # --- step 2: summaries + cheap pre-filter ----------------------------
    all_uids = [u for ids in hits.values() for u in ids]
    print(f"[phase 2] esummary for {len(set(all_uids))} records")
    summaries = client.summaries(all_uids, batch)

    dropped: list[dict[str, Any]] = []
    selected: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen_accessions: set[str] = set()
    for (species, marker), ids in hits.items():
        mcfg = markers[marker]
        candidates = []
        for uid in ids:
            s = summaries.get(uid, {})
            acc = s.get("accessionversion") or s.get("caption") or uid
            if s.get("_missing"):
                dropped.append(_drop(species, marker, acc, "summary", "no_summary", ""))
                continue
            reason = check_name(s.get("organism"), s.get("title"), species, allow_mismatch)
            if reason is None and (s.get("moltype") or "dna") != "dna":
                reason = "not_dna"
            if reason is None and int(s.get("slen") or 0) < mcfg["min_length"]:
                reason = "too_short"
            if reason is None and acc in seen_accessions:
                reason = "duplicate_accession"
            if reason:
                dropped.append(_drop(species, marker, acc, "summary", reason, f"{s.get('organism')} | {s.get('title')}"))
                continue
            seen_accessions.add(acc)
            candidates.append((int(s.get("slen") or 0), acc))
        candidates.sort(key=lambda t: -t[0])  # longest sequences first
        for _, acc in candidates[cap:]:
            dropped.append(_drop(species, marker, acc, "selection", "not_selected_cap", f"cap={cap}"))
        selected[(species, marker)] = [{"accession": acc} for _, acc in candidates[:cap]]

    # --- step 3: efetch full records of the kept accessions --------------
    to_fetch = [r["accession"] for recs in selected.values() for r in recs]
    print(f"[phase 2] efetch {len(to_fetch)} GenBank records")
    texts = client.genbank_records(to_fetch, batch)

    table: list[dict[str, Any]] = []
    fasta: dict[str, list[tuple[str, str]]] = {m: [] for m in markers}
    info = {r["species"]: r for r in species_rows}
    for (species, marker), recs in selected.items():
        mcfg = markers[marker]
        for r in recs:
            acc = r["accession"]
            parsed = parse_genbank(texts.get(acc, ""))
            if parsed is None:
                dropped.append(_drop(species, marker, acc, "download", "record_not_returned", ""))
                continue
            # Re-check the name with the full record, then the sequence itself.
            reason = check_name(parsed["organism"], parsed["definition"], species, allow_mismatch)
            if reason is None:
                reason = check_sequence(parsed["sequence"], mcfg["min_length"], mcfg["max_n_fraction"])
            if reason:
                dropped.append(_drop(species, marker, acc, "download", reason, parsed["definition"]))
                continue
            seq = parsed["sequence"]
            table.append({
                "species": species,
                "family": info[species]["family"],
                "genus": info[species]["genus"],
                "marker": marker,
                "accession": acc,
                "length": len(seq),
                "source_title": parsed["reference_title"] or parsed["definition"],
                "definition": parsed["definition"],
                "organism": parsed["organism"],
                "n_fraction": round(n_fraction(seq), 5),
                "country": parsed["country"],
                "voucher": parsed["voucher"],
            })
            fasta[marker].append((f"{acc} {species}", seq))

    write_outputs(table, fasta, dropped)
    reasons: dict[str, int] = {}
    for d in dropped:
        reasons[d["reason"]] = reasons.get(d["reason"], 0) + 1
    print(f"[phase 2] kept {len(table)} sequences, dropped {len(dropped)}: {reasons}")
    print(f"[phase 2] NCBI network calls this run: {client.network_calls}")


def _drop(species: str, marker: str, accession: str, stage: str, reason: str, detail: str) -> dict[str, Any]:
    return {"species": species, "marker": marker, "accession": accession,
            "stage": stage, "reason": reason, "detail": detail}


def write_outputs(table: list[dict[str, Any]], fasta: dict[str, list[tuple[str, str]]], dropped: list[dict[str, Any]]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    SEQUENCES_DIR.mkdir(parents=True, exist_ok=True)
    table.sort(key=lambda r: (r["family"], r["species"], r["marker"], r["accession"]))
    for r in table:
        r.setdefault("is_turkey", int(str(r.get("country", "")).lower().startswith(("turkey", "türkiye"))))
        r.setdefault("matched_via", "accepted")
        r.setdefault("source", "NCBI")
    with open(SEQUENCE_TABLE_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=TABLE_COLUMNS)
        w.writeheader()
        w.writerows(table)
    with open(DROPPED_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DROPPED_COLUMNS)
        w.writeheader()
        w.writerows(dropped)
    for marker, items in fasta.items():
        with open(SEQUENCES_DIR / f"{marker}.fasta", "w", encoding="utf-8") as fh:
            for header, seq in sorted(items):
                fh.write(f">{header}\n")
                for i in range(0, len(seq), 70):
                    fh.write(seq[i : i + 70] + "\n")
