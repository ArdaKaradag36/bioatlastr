import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from names_lib import include_non_commercial, source_info

def test_tiers_and_licence_classes():
    assert source_info("wikidata")[1:3] == ("A", "open")
    assert source_info("gbif:Catalogue of Life")[1:3] == ("A", "open")
    assert source_info("trwiki")[1] == "A"
    assert source_info("inaturalist")[1:3] == ("B", "non-commercial")
    assert source_info("gbif:IUCN Red List")[1:3] == ("B", "non-commercial")
    for c in ("gbif:World Register of Marine Species", "gbif:World Register of Introduced Marine Species (WRiMS)",
              "gbif:DAISIE - Inventory of alien invasive species in Europe", "gbif:Divriği-Kars-Georgia Border Railway Line Rehabilitation and ",
              "gbif:Some unreviewed dataset"):
        assert source_info(c)[1] == "C"

def test_non_commercial_flag(monkeypatch):
    monkeypatch.setenv("NAMES_INCLUDE_NON_COMMERCIAL", "0")
    assert include_non_commercial() is False
    monkeypatch.setenv("NAMES_INCLUDE_NON_COMMERCIAL", "1")
    assert include_non_commercial() is True
    monkeypatch.delenv("NAMES_INCLUDE_NON_COMMERCIAL")
    assert include_non_commercial() is False  # config default: open licences only

def test_privacy_sanitizer():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
    from privacy_lib import sanitize_sequence
    r = sanitize_sequence({"voucher": "Eric Schuettpelz 1741", "country": "USA:California, Siskiyou Co.: @ 3 mi SW of Scott",
                           "definition": "Eragrostis voucher 06-PMP-19738 rbcL gene, partial cds", "accession": "MF1"}, "Eragrostis", "rbcL")
    assert r["voucher"] == "" and r["country"] == "USA" and "06-PMP" not in r["definition"] and r["accession"] == "MF1"
    ok = sanitize_sequence({"definition": "Pinus rbcL gene, partial cds; chloroplast", "country": "Turkey"}, "Pinus", "rbcL")
    assert ok["definition"].startswith("Pinus rbcL gene") and ok["country"] == "Turkey"
