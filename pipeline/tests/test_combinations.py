import numpy as np

from barcode_atlas.discrimination import combined_species_distance, species_level_status

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


def test_missing_species_in_one_marker_is_ignored_for_that_marker():
    m1 = (["A", "B"], mat([[0.01, 0.1], [0.1, 0.01]]))
    m2 = (["A", "C"], mat([[0.02, 0.2], [0.2, 0.02]]))
    names, comb = combined_species_distance({"x": m1, "y": m2}, ["x", "y"])
    i = {n: k for k, n in enumerate(names)}
    assert np.isnan(comb[i["B"], i["C"]])           # never compared in any marker
    assert abs(comb[i["A"], i["B"]] - 0.1) < 1e-9   # only marker x contributes
    assert abs(comb[i["A"], i["A"]] - 0.015) < 1e-9
