"""Phase 1 logic tested with a fake GBIF client (no network needed)."""

import csv

from barcode_atlas import gbif
from barcode_atlas.http_cache import DiskCache, RateLimiter, cache_key


class FakeClient:
    """Returns canned GBIF answers keyed by URL."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def get_json(self, url, params=None):
        self.calls.append((url, params))
        for key, value in self.answers.items():
            if url.endswith(key):
                return value
        return {"_not_found": True}


def species_record(key, name, status="ACCEPTED", rank="SPECIES", family="Fagaceae", vern=None):
    return {
        "key": key, "canonicalName": name, "rank": rank, "taxonomicStatus": status,
        "genus": name.split()[0], "family": family, "familyKey": 4689,
        "authorship": "L.", "vernacularName": vern,
    }


def make_client():
    return FakeClient({
        "/species/match": {"usageKey": 4689, "rank": "FAMILY", "matchType": "EXACT"},
        "/occurrence/search": {"facets": [{"counts": [
            {"name": "1", "count": 500},   # Quercus robur
            {"name": "2", "count": 300},   # synonym -> must be skipped
            {"name": "3", "count": 100},   # hybrid -> must be skipped
            {"name": "4", "count": 50},    # Quercus cerris
            {"name": "5", "count": 1},     # below min_occurrences
        ]}]},
        "/species/1": species_record(1, "Quercus robur", vern="Pedunculate Oak"),
        "/species/2": species_record(2, "Quercus pedunculata", status="SYNONYM"),
        "/species/3": species_record(3, "Quercus x rosacea"),
        "/species/4": species_record(4, "Quercus cerris"),
        "/species/5": species_record(5, "Quercus rare"),
        "/species/1/vernacularNames": {"results": [
            {"vernacularName": "Saplı meşe", "language": "tur"},
            {"vernacularName": "English oak", "language": "eng"},
        ]},
        "/species/4/vernacularNames": {"results": []},
    })


def test_fetch_family_species_filters_and_names():
    rows = gbif.fetch_family_species(make_client(), "Fagaceae", "TR", max_species=None, min_occurrences=2)
    assert [r["species"] for r in rows] == ["Quercus robur", "Quercus cerris"]
    robur = rows[0]
    assert robur["common_name_tr"] == "Saplı meşe"
    assert robur["common_name_en"] == "Pedunculate Oak"   # GBIF preferred name wins
    assert robur["occurrences_tr"] == 500
    assert rows[1]["common_name_tr"] == ""


def test_max_species_keeps_most_frequent():
    rows = gbif.fetch_family_species(make_client(), "Fagaceae", "TR", max_species=1, min_occurrences=1)
    assert [r["species"] for r in rows] == ["Quercus robur"]


def test_write_species_csv(tmp_path):
    rows = gbif.fetch_family_species(make_client(), "Fagaceae", "TR", None, 2)
    out = tmp_path / "species.csv"
    gbif.write_species_csv(rows, out)
    with open(out, encoding="utf-8") as fh:
        read = list(csv.DictReader(fh))
    assert list(read[0].keys()) == gbif.SPECIES_COLUMNS
    assert len(read) == 2


def test_disk_cache_roundtrip(tmp_path):
    cache = DiskCache("test", root=tmp_path)
    key = cache_key("url", {"a": 1})
    assert cache.get(key) is None
    cache.set(key, {"x": [1, 2]})
    assert cache.get(key) == {"x": [1, 2]}
    assert cache_key("url", {"a": 1}) == key  # stable


def test_rate_limiter_waits(monkeypatch):
    slept = []
    t = [0.0]
    monkeypatch.setattr("barcode_atlas.http_cache.time.monotonic", lambda: t[0])
    monkeypatch.setattr("barcode_atlas.http_cache.time.sleep", lambda s: (slept.append(s), t.__setitem__(0, t[0] + s)))
    limiter = RateLimiter(0.5)
    limiter.wait()          # first call: no wait (last = 0, now = 0 -> waits 0.5 once)
    limiter.wait()
    assert all(abs(s - 0.5) < 1e-9 for s in slept)
