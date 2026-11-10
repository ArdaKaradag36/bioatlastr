import numpy as np

from barcode_atlas.analysis import COMBINATION_DEFINITION, combination_table
from barcode_atlas.discrimination import combined_species_distance, species_level_status
import pandas as pd

INF = np.inf


def mat(rows):
    return np.array(rows, dtype=float)


def test_single_marker_status():
    # A has 2 seqs (intra 0.01), B 2 seqs (intra 0.02), C 1 seq; A-B 0.05, A-C 0.03, B-C 0.015
    sd = mat([[0.01, 0.05, 0.03], [0.05, 0.02, 0.015], [0.03, 0.015, INF]])
    names, comb = combined_species_distance({"m": (["A", "B", "C"], sd)}, ["m"])
    st = species_level_status(names, comb)
    assert st == {"A": "success", "B": "fail"}  # B: nearest other (C) 0.015 < intra 0.02; C has no intra


def test_tie_is_ambiguous():
    sd = mat([[0.0, 0.0], [0.0, 0.0]])
    names, comb = combined_species_distance({"m": (["A", "B"], sd)}, ["m"])
    assert species_level_status(names, comb) == {"A": "ambiguous", "B": "ambiguous"}


def test_combination_resolves_what_one_marker_cannot():
    # marker 1: A and B identical (0); marker 2 separates them (0.04)
    m1 = (["A", "B"], mat([[0.0, 0.0], [0.0, 0.0]]))
    m2 = (["A", "B"], mat([[0.0, 0.04], [0.04, 0.0]]))
    names, comb = combined_species_distance({"x": m1, "y": m2}, ["x", "y"])
    assert comb[0, 1] == 0.02 and comb[0, 0] == 0.0
    assert species_level_status(names, comb) == {"A": "success", "B": "success"}


def test_only_species_in_all_markers_are_kept():
    m1 = (["A", "B"], mat([[0.01, 0.1], [0.1, 0.01]]))
    m2 = (["A", "C"], mat([[0.02, 0.2], [0.2, 0.02]]))
    names, comb = combined_species_distance({"x": m1, "y": m2}, ["x", "y"])
    assert names == ["A"]  # B and C lack the other marker
    assert comb.shape == (1, 1)
    assert abs(comb[0, 0] - 0.015) < 1e-9
    assert species_level_status(names, comb) == {}  # no competitor


def test_union_mode_allows_partial_overlap_when_requested():
    m1 = (["A", "B"], mat([[0.01, 0.1], [0.1, 0.01]]))
    m2 = (["A", "C"], mat([[0.02, 0.2], [0.2, 0.02]]))
    names, comb = combined_species_distance(
        {"x": m1, "y": m2}, ["x", "y"], min_markers=1, require_all_markers=False,
    )
    i = {n: k for k, n in enumerate(names)}
    assert np.isnan(comb[i["B"], i["C"]])
    assert abs(comb[i["A"], i["B"]] - 0.1) < 1e-9
    assert abs(comb[i["A"], i["A"]] - 0.015) < 1e-9


def test_min_markers_requires_enough_overlap():
    # A-B finite in both markers; mean needs both when min_markers=2
    m1 = (["A", "B"], mat([[0.0, 0.10], [0.10, 0.0]]))
    m2 = (["A", "B"], mat([[0.0, 0.30], [0.30, 0.0]]))
    names, comb = combined_species_distance({"x": m1, "y": m2}, ["x", "y"], min_markers=2)
    assert abs(comb[0, 1] - 0.20) < 1e-9
    names2, comb2 = combined_species_distance({"x": m1, "y": m2}, ["x", "y"], min_markers=3)
    assert np.isnan(comb2[0, 1])  # only 2 markers exist


def test_not_intersection_of_marker_successes():
    # x succeeds, y fails for A; intersection of per-marker successes would reject A.
    # Mean distance still succeeds — combined power, not AND of marker flags.
    m1 = (["A", "B"], mat([[0.01, 0.10], [0.10, 0.01]]))  # success
    m2 = (["A", "B"], mat([[0.10, 0.05], [0.05, 0.10]]))  # fail
    assert species_level_status(*combined_species_distance({"x": m1}, ["x"]))["A"] == "success"
    assert species_level_status(*combined_species_distance({"y": m2}, ["y"]))["A"] == "fail"
    # mean intra (0.01+0.10)/2=0.055; mean inter (0.10+0.05)/2=0.075 -> success
    st = species_level_status(*combined_species_distance({"x": m1, "y": m2}, ["x", "y"]))
    assert st["A"] == "success"


def test_combination_table_definition_and_n():
    # two groups, three species shared across both markers
    sd = mat([[0.01, 0.10], [0.10, 0.01]])
    species_level = {
        ("Fam", "rbcL"): (["A", "B"], sd),
        ("Fam", "matK"): (["A", "B"], sd),
    }
    species_df = pd.DataFrame([
        {"species": "A", "family": "Fam"},
        {"species": "B", "family": "Fam"},
        {"species": "C", "family": "Fam"},
    ])
    out = combination_table(species_level, species_df, ["rbcL", "matK"])
    row = out[(out["scope"] == "ALL") & (out["combination"] == "rbcL+matK")].iloc[0]
    assert row["definition"] == COMBINATION_DEFINITION == "strict_combined_distance"
    assert int(row["species_evaluated"]) == 2
    assert int(row["success"]) == 2
    assert int(row["rbcL_alone_success"]) == 2
    assert int(row["matK_alone_success"]) == 2
    assert abs(float(row["rbcL_alone_success_rate"]) - 1.0) < 1e-9


def test_alone_columns_use_combination_species_subset():
    # rbcL alone separates A from B; matK alone fails for A (inter closer than intra).
    # Combined mean can still succeed. Alone rates must be on the shared A,B set only.
    rbcl = (["A", "B", "C"], mat([
        [0.01, 0.10, 0.20],
        [0.10, 0.01, 0.20],
        [0.20, 0.20, 0.01],
    ]))
    matk = (["A", "B"], mat([
        [0.10, 0.05],
        [0.05, 0.10],
    ]))
    species_level = {("Fam", "rbcL"): rbcl, ("Fam", "matK"): matk}
    species_df = pd.DataFrame([
        {"species": "A", "family": "Fam"},
        {"species": "B", "family": "Fam"},
        {"species": "C", "family": "Fam"},
    ])
    out = combination_table(species_level, species_df, ["rbcL", "matK", "ITS"])
    row = out[(out["scope"] == "ALL") & (out["combination"] == "rbcL+matK")].iloc[0]
    assert int(row["species_evaluated"]) == 2  # C lacks matK
    assert int(row["rbcL_alone_success"]) == 2
    assert abs(float(row["rbcL_alone_success_rate"]) - 1.0) < 1e-9
    assert int(row["matK_alone_success"]) == 0
    assert abs(float(row["matK_alone_success_rate"]) - 0.0) < 1e-9
    # Alone rates use the same n as the combination row.
    assert abs(float(row["rbcL_alone_success"]) / float(row["species_evaluated"]) - float(row["rbcL_alone_success_rate"])) < 1e-9
    assert pd.isna(row["ITS_alone_success"]) and pd.isna(row["ITS_alone_success_rate"])
    single = out[(out["scope"] == "ALL") & (out["combination"] == "rbcL")].iloc[0]
    assert int(single["rbcL_alone_success"]) == int(single["success"])
    assert pd.isna(single["matK_alone_success"])
