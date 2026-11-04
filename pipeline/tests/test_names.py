from barcode_atlas.names import build_name_index, match_record

ACC = ["Quercus robur", "Quercus petraea", "Sideritis montana"]
SYN = [("Burgsdorfia montana", "Sideritis montana"), ("Quercus sessiliflora", "Quercus petraea"),
       ("Foo bar", "Quercus robur"), ("Foo bar", "Quercus petraea"), ("Quercus fake", "Not Listed")]


def idx():
    return build_name_index(ACC, SYN)


def test_accepted_and_infraspecific():
    assert match_record("Quercus robur", "x", idx()) == ("Quercus robur", "accepted", None)
    assert match_record("Quercus robur subsp. robur", "x", idx())[0] == "Quercus robur"


def test_synonym_is_resolved():
    assert match_record("Quercus sessiliflora", "x", idx()) == ("Quercus petraea", "synonym", None)


def test_ambiguous_synonym_and_foreign_target_ignored():
    assert match_record("Foo bar", "x", idx())[2] == "ambiguous_synonym"
    assert match_record("Quercus fake", "x", idx())[2] == "unmatched_name"


def test_bad_names_rejected_with_reason():
    i = idx()
    assert match_record("Quercus sp.", "x", i)[2] == "ambiguous_sp"
    assert match_record("Quercus cf. robur", "x", i)[2] == "ambiguous_cf"
    assert match_record("Quercus x rosacea", "x", i)[2] == "hybrid"
    assert match_record("Quercus robur", "UNVERIFIED: Quercus", i)[2] == "unverified"
    assert match_record("uncultured plant", "x", i)[2] == "not_binomial"
    assert match_record(None, "x", i)[2] == "no_organism"
    assert match_record("Quercus alba", "x", i)[2] == "unmatched_name"


def test_genus_alias_and_gender_variant():
    # WCVP: accepted "Acinos arvensis"-type names whose genus ENA files under Clinopodium
    index = build_name_index(["Acinos arvensis", "Quercus alba"], [])
    alias = {"Clinopodium": ["Acinos"]}
    assert match_record("Clinopodium arvense", "x", index)[2] == "unmatched_name"          # no fallback -> unmatched
    assert match_record("Clinopodium arvense", "x", index, alias) == ("Acinos arvensis", "genus_synonym", None)
    assert match_record("Quercus album", "x", index) == ("Quercus alba", "epithet_variant", None)
    # two WCVP genera behind one ENA genus pointing to different accepted species -> ambiguous
    index2 = build_name_index(["Acinos arvensis", "Ziziphora arvensis"], [])
    assert match_record("Clinopodium arvense", "x", index2, {"Clinopodium": ["Acinos", "Ziziphora"]})[2] == "ambiguous_synonym"
    assert match_record("Clinopodium zzz", "x", index, alias)[2] == "unmatched_name"
