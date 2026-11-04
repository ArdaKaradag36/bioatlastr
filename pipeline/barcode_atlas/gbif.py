"""Phase 1: accepted plant species that occur in Turkey, from the GBIF API."""

from __future__ import annotations

import csv
import re
from typing import Any

from .http_cache import CachedJsonClient
from .paths import DATA, SPECIES_CSV

GBIF = "https://api.gbif.org/v1"
SPECIES_COLUMNS = [
    "species",
    "genus",
    "family",
    "gbif_key",
    "family_gbif_key",
    "authorship",
    "occurrences_tr",
    "common_name_en",
    "common_name_tr",
]

# "Quercus robur" is fine; "Quercus x rosacea", "Quercus × rosacea", "Quercus sp." are not.
BINOMIAL_RE = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+$")


def is_clean_binomial(name: str | None) -> bool:
    """True for a plain two-word Latin species name (no hybrids, no subspecies)."""
    return bool(name) and bool(BINOMIAL_RE.match(name)) and " x " not in name


def match_family(client: CachedJsonClient, family: str) -> int:
    """Find the GBIF backbone key of an accepted plant family."""
    data = client.get_json(f"{GBIF}/species/match", {"name": family, "rank": "FAMILY", "kingdom": "Plantae"})
    if data.get("rank") != "FAMILY" or data.get("matchType") == "NONE":
        raise ValueError(f"Family not found in GBIF backbone: {family}")
    # Follow synonyms to the accepted family if needed.
    return int(data.get("acceptedUsageKey") or data["usageKey"])


def turkish_species_counts(client: CachedJsonClient, family_key: int, country: str) -> list[tuple[int, int]]:
    """(speciesKey, occurrence count) for the family in the country, most frequent first.

    Uses the occurrence facet so we only get species with at least one record in Turkey.
    Paginated because a facet answer is limited in size.
    """
    out: list[tuple[int, int]] = []
    offset, page = 0, 1000
    while True:
        data = client.get_json(
            f"{GBIF}/occurrence/search",
            {
                "country": country,
                "taxonKey": family_key,
                "occurrenceStatus": "PRESENT",
                "limit": 0,
                "facet": "speciesKey",
                "facetLimit": page,
                "facetOffset": offset,
            },
        )
        facets = data.get("facets") or []
        counts = facets[0]["counts"] if facets else []
        out.extend((int(c["name"]), int(c["count"])) for c in counts)
        if len(counts) < page:
            break
        offset += page
    out.sort(key=lambda t: -t[1])  # already sorted by GBIF, but be explicit
    return out


def pick_common_names(species: dict[str, Any], vernaculars: dict[str, Any]) -> tuple[str, str]:
    """Return (English, Turkish) common names when GBIF knows them, else empty strings."""
    english = species.get("vernacularName") or ""
    turkish = ""
    for item in vernaculars.get("results", []):
        lang = (item.get("language") or "").lower()
        name = item.get("vernacularName") or ""
        if not name:
            continue
        if lang in ("tur", "tr") and not turkish:
            turkish = name
        elif lang in ("eng", "en") and not english:
            english = name
    return english.strip(), turkish.strip()


def parse_species_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Keep only accepted, plain species names. Return None to skip."""
    if record.get("_not_found"):
        return None
    if record.get("rank") != "SPECIES" or record.get("taxonomicStatus") != "ACCEPTED":
        return None
    name = record.get("canonicalName")
    if not is_clean_binomial(name):
        return None
    return {
        "species": name,
        "genus": record.get("genus") or name.split()[0],
        "family": record.get("family") or "",
        "gbif_key": record["key"],
        "family_gbif_key": record.get("familyKey") or "",
        "authorship": record.get("authorship") or "",
    }


def fetch_family_species(
    client: CachedJsonClient,
    family: str,
    country: str,
    max_species: int | None,
    min_occurrences: int,
) -> list[dict[str, Any]]:
    """All accepted species of one family recorded in the country."""
    family_key = match_family(client, family)
    counts = turkish_species_counts(client, family_key, country)
    print(f"  {family}: {len(counts)} species keys with records in {country}")

    rows: list[dict[str, Any]] = []
    for species_key, n_occ in counts:
        if n_occ < min_occurrences:
            continue
        if max_species is not None and len(rows) >= max_species:
            break
        raw = client.get_json(f"{GBIF}/species/{species_key}")
        rec = parse_species_record(raw)
        if rec is None:
            continue
        # Make sure GBIF did not return a species of another family (synonym moves).
        if rec["family"] != family:
            continue
        vern = client.get_json(f"{GBIF}/species/{species_key}/vernacularNames", {"limit": 1000})
        en, tr = pick_common_names(raw, vern)
        rec.update({"occurrences_tr": n_occ, "common_name_en": en, "common_name_tr": tr})
        rows.append(rec)
    return rows


def write_species_csv(rows: list[dict[str, Any]], path=SPECIES_CSV) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SPECIES_COLUMNS)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["family"], r["species"])):
            writer.writerow({k: row.get(k, "") for k in SPECIES_COLUMNS})


def run_phase1(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    # GBIF sometimes answers 503 for a while: be patient (back-off up to 60 s per retry)
    client = CachedJsonClient("gbif", cfg["gbif"]["min_interval"], max_retries=cfg["gbif"].get("max_retries", 10))
    all_rows: list[dict[str, Any]] = []
    for family in cfg["families"]:
        print(f"[phase 1] {family}")
        rows = fetch_family_species(
            client,
            family,
            cfg["gbif"]["country"],
            cfg["max_species_per_family"],
            cfg["min_occurrences_in_turkey"],
        )
        print(f"  -> {len(rows)} accepted species kept")
        all_rows.extend(rows)
    write_species_csv(all_rows)
    print(f"[phase 1] wrote {SPECIES_CSV} ({len(all_rows)} species); "
          f"network calls: {client.network_calls}, cache hits: {client.cache_hits}")
    return all_rows
