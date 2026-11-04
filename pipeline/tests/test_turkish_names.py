import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from names_lib import (ascii_key, bad_title, clean, flag_ambiguous, fold_key, is_latin_like, merge_variants, resolve_name, tr_lower)

GEN = {"Quercus", "Pinus", "Taraxacum"}

def test_turkish_case_folding():
    assert tr_lower("KIZILÇAM") == "kızılçam" and tr_lower("İĞDE") == "iğde" and tr_lower("ISIRGAN") == "ısırgan"
    assert fold_key("Kızılçam") == fold_key("KIZILÇAM") == fold_key("kızılçam")
    assert fold_key("IĞDIR") != fold_key("İĞDİR")           # I/ı and İ/i stay different letters
    # diacritic-insensitive search key: all three spellings of the same word are equal
    assert ascii_key("kizilcam") == ascii_key("KIZILÇAM") == ascii_key("Kızılçam")

def test_clean_and_dedupe_keeps_turkish_letters():
    assert clean("  Kara  Hindiba \u00a0") == "Kara Hindiba"
    assert merge_variants(["Sacli Mese", "Saçlı Meşe", "saçlı meşe", "Zeytin", "ZEYTİN"]) == ["Saçlı Meşe", "Zeytin"]
    assert clean("e\u0301") == "\u00e9"                       # NFC

def test_drop_names_identical_to_latin():
    assert is_latin_like("Quercus cerris", "Quercus cerris", GEN)
    assert is_latin_like("quercus cerris", "Quercus cerris", GEN)
    assert is_latin_like("Pinus nigra", "Quercus cerris", GEN)   # another Latin binomial
    assert not is_latin_like("Saçlı meşe", "Quercus cerris", GEN)
    assert not is_latin_like("Kızılçam", "Pinus brutia", GEN)
    assert bad_title("Papatya (cins)") and bad_title("Bitki listesi 2020") and not bad_title("Kızılçam")

def test_synonym_maps_to_accepted_species():
    species, syn = {"Clinopodium arvense"}, {"Acinos arvensis": "Clinopodium arvense"}
    assert resolve_name("Acinos arvensis", "species", species, syn, set(), set()) == ("Clinopodium arvense", "synonym")
    assert resolve_name("Clinopodium arvense", "species", species, syn, set(), set()) == ("Clinopodium arvense", "accepted")
    assert resolve_name("Foo bar", "species", species, syn, set(), set()) == (None, None)
    assert resolve_name("Quercus", "genus", species, syn, {"Quercus"}, set()) == ("Quercus", "accepted")

def test_ambiguity_flag_many_to_many():
    assign = {ascii_key("Kekik"): {"Thymus a", "Thymus b", "Origanum c"}, ascii_key("Kızılçam"): {"Pinus brutia"}}
    assert flag_ambiguous(assign) == {"kekik": True, "kizilcam": False}
