import json

from barcode_atlas.ena import (build_query, classify_record, is_turkey, marker_reason, parse_fasta, parse_tsv,
                               pick_genus_entry, select_sequences)
from barcode_atlas.config import load_config
from pathlib import Path

CFG = load_config(Path(__file__).parents[1] / "config.yaml")


def test_turkey_flag():
    assert is_turkey("Turkey: Izmir") and is_turkey("Türkiye") and is_turkey("Turkey")
    assert not is_turkey("Malaysia:Turkey Hill") and not is_turkey("") and not is_turkey(None)


def test_genus_homonym_is_ignored():
    entries = [
        {"taxId": "1", "scientificName": "Nama", "rank": "genus", "lineage": "Eukaryota; Metazoa; "},
        {"taxId": "2", "scientificName": "Nama", "rank": "genus", "lineage": "Eukaryota; Viridiplantae; "},
    ]
    assert pick_genus_entry(entries, "Nama") == 2
    assert pick_genus_entry(entries[:1], "Nama") is None


def test_query_contains_tax_tree_markers_and_limits():
    q = build_query(3511, CFG["markers"])
    assert q.startswith("tax_tree(3511) AND (description=\"*rbcL*\"")
    assert '"*matK*"' in q and '"*internal transcribed spacer*"' in q
    assert "base_count>=350" in q and "base_count<=2000" in q
    q1 = build_query(3511, CFG["markers"]["rbcL"])
    assert "base_count>=400" in q1 and "base_count<=1600" in q1 and "matK" not in q1


def test_classify_record():
    mk = CFG["markers"]
    assert classify_record("Quercus rbcL gene, partial cds", 900, mk) == ("rbcL", None)
    assert classify_record("Quercus rbcL gene, partial cds", 100, mk) == ("rbcL", "too_short")
    assert classify_record("Quercus maturase K (matK) gene", 3000, mk) == ("matK", "too_long")
    assert classify_record("Quercus ITS1, 5.8S rRNA, ITS2", 650, mk) == ("ITS", None)
    assert classify_record("Quercus rbcL and matK genes", 900, mk) == (None, "multi_marker_record")
    assert classify_record("Quercus trnL intron", 900, mk) == (None, "marker_not_in_description")
    assert classify_record("Quercus atpB-rbcL intergenic spacer", 900, mk) == ("rbcL", "wrong_region_or_genome")


def test_marker_regexes_drop_spacers_and_genomes():
    r = CFG["markers"]["rbcL"]
    assert marker_reason("Quercus ilex chloroplast rbcL gene for ribulose 1,5-bisphosphate carboxylase", r) is None
    assert marker_reason("Quercus mongolica atpB-rbcL intergenic spacer, haplotype", r) == "wrong_region_or_genome"
    assert marker_reason("Quercus chloroplast, complete genome", r) is not None
    its = CFG["markers"]["ITS"]
    assert marker_reason("Pinus nigra 18S rRNA gene, ITS1, 5.8S rRNA gene, ITS2", its) is None
    assert marker_reason("Pinus nigra internal transcribed spacer 1, partial sequence", its) is None
    assert marker_reason("Pinus nigra trnL-F intergenic spacer", its) == "marker_not_in_description"
    mk_all = CFG["markers"]
    # pure 5.8S / nrDNA / 18S-26S records and non-ITS regions pulled in by the broader query are not ITS records
    assert classify_record("Rosa canina 5.8S ribosomal RNA gene, partial sequence", 400, mk_all) == (None, "marker_not_in_description")
    assert classify_record("Rosa canina 18S-26S nrDNA, partial sequence", 700, mk_all) == (None, "marker_not_in_description")
    assert classify_record("Rosa canina ITS1 and 5.8S rRNA, partial", 700, mk_all) == ("ITS", None)
    assert classify_record("Rosa canina external transcribed spacer, ETS", 700, mk_all)[1] is not None
    assert classify_record("Rosa canina 26S rRNA intergenic spacer ITS", 700, mk_all)[1] == "wrong_region_or_genome"
    mk = CFG["markers"]["matK"]
    assert marker_reason("Pinus nigra maturase K (matK) gene, partial cds", mk) is None


def test_parse_fasta_and_tsv():
    got = parse_fasta(">ENA|AB1|AB1.1 Quercus\nACGT\nAC\n>ENA|AB2|AB2.1 x\nGG\n")
    assert got == {"AB1": "ACGTAC", "AB2": "GG"}
    rows = parse_tsv("accession\tcountry\nAB1\tTurkey: x\nAB2\t\n")
    assert rows[0]["country"] == "Turkey: x" and rows[1]["country"] == ""


def rec(acc, seq, tr=False, n=None):
    return {"accession": acc, "sequence": seq, "length": n or len(seq), "is_turkey": tr}


def test_selection_prefers_turkey_limits_duplicates_and_cap():
    recs = [rec("A", "AAAA"), rec("B", "AAAA"), rec("C", "AAAA"), rec("D", "CCCC", tr=True), rec("E", "GGGGG")]
    kept, dropped = select_sequences(recs, cap=10, max_identical=2)
    assert [r["accession"] for r in kept][0] == "D"          # Turkish record first
    assert sum(r["sequence"] == "AAAA" for r in kept) == 2   # max 2 identical copies
    assert ("C", "near_duplicate") in [(r["accession"], w) for r, w in dropped]
    kept, dropped = select_sequences(recs, cap=2, max_identical=2)
    assert len(kept) == 2 and {w for _, w in dropped} >= {"not_selected_cap"}
    assert len({r["sequence"] for r in kept}) == 2           # distinct sequences are preferred over copies


def test_resolve_genus_scientific_then_any_name():
    from barcode_atlas.ena import resolve_genus

    plant = lambda tid, name: json.dumps([{"taxId": str(tid), "scientificName": name, "rank": "genus", "lineage": "Eukaryota; Viridiplantae; "}])

    class Fake:
        def get_text(self, url, params=None, timeout=0):
            name = url.rsplit("/", 1)[1]
            if "scientific-name" in url:
                return plant(3511, "Quercus") if name == "Quercus" else "[ ]"
            return plant(3754, "Prunus") if name == "Amygdalus" else "[ ]"

    assert resolve_genus(Fake(), "Quercus") == (3511, "Quercus", "scientific-name")
    assert resolve_genus(Fake(), "Amygdalus") == (3754, "Prunus", "any-name")
    assert resolve_genus(Fake(), "Abiga") == (None, "", "none")


def test_missing_description_does_not_crash():
    from barcode_atlas.ena import parse_tsv, marker_reason_include
    mk = CFG["markers"]
    assert classify_record(None, 700, mk) == (None, "missing_description")
    assert classify_record("   ", 700, mk) == (None, "missing_description")
    assert marker_reason_include(None, mk["rbcL"]) == "marker_not_in_description"
    assert marker_reason(None, mk["rbcL"]) is not None
    # short / malformed TSV lines give None values in csv.DictReader -> normalised to ""
    rows = parse_tsv("accession\tdescription\tscientific_name\tbase_count\nAB1\nAB2\tQuercus rbcL\tQuercus ilex\t700\textra")
    assert rows[0]["description"] == "" and rows[0]["scientific_name"] == ""
    assert rows[1]["description"] == "Quercus rbcL" and None not in rows[1]
