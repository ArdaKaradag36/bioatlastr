"""Tests for the discrimination (threshold-free nearest-neighbour) logic and nearest relatives."""

import numpy as np

from barcode_atlas.discrimination import (
    best_close_match,
    group_by_species,
    nearest_relatives,
    species_distance_matrix,
    summarize_bcm,
    zero_distance_pairs,
)


def matrix(rows):
    return np.array(rows, dtype=float)


def status_of(results, species):
    return [r["status"] for r in results if r["species"] == species]


def test_success_when_nearest_is_same_species():
    # A1 A2 close together, B far away
    species = ["A", "A", "B", "B"]
    d = matrix([
        [0.0, 0.01, 0.20, 0.21],
        [0.01, 0.0, 0.22, 0.20],
        [0.20, 0.22, 0.0, 0.02],
        [0.21, 0.20, 0.02, 0.0],
    ])
    res = best_close_match(d, species)
    assert [r["status"] for r in res] == ["success"] * 4
    summary = summarize_bcm(res)
    assert summary["success_rate"] == 1.0
    assert summary["species_success"] == 2


def test_fail_when_nearest_is_other_species():
    # A2 is closer to B1 than to A1 -> A2 fails (and B1 too)
    species = ["A", "A", "B", "B"]
    d = matrix([
        [0.0, 0.10, 0.30, 0.30],
        [0.10, 0.0, 0.02, 0.30],
        [0.30, 0.02, 0.0, 0.25],
        [0.30, 0.30, 0.25, 0.0],
    ])
    res = best_close_match(d, species)
    assert status_of(res, "A") == ["success", "fail"] or status_of(res, "A") == ["fail", "fail"]
    assert res[1]["status"] == "fail"       # A2 -> nearest is B1
    assert res[2]["status"] == "fail"       # B1 -> nearest is A2
    assert res[3]["status"] == "success"    # B2 -> nearest conspecific B1 (0.25) < A (0.30)
    s = summarize_bcm(res)
    assert s["fail"] >= 2 and s["species_success"] == 0


def test_tie_between_same_and_other_species_is_ambiguous():
    species = ["A", "A", "B", "B"]
    d = matrix([
        [0.0, 0.05, 0.05, 0.30],
        [0.05, 0.0, 0.30, 0.30],
        [0.05, 0.30, 0.0, 0.10],
        [0.30, 0.30, 0.10, 0.0],
    ])
    res = best_close_match(d, species)
    assert res[0]["status"] == "ambiguous"  # A1: A2 and B1 both at 0.05


def test_identical_sequences_of_different_species_are_ambiguous_not_success():
    species = ["A", "A", "B"]
    d = matrix([
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ])
    res = best_close_match(d, species)
    assert [r["status"] for r in res] == ["ambiguous", "ambiguous"]  # B has 1 sequence: not evaluated


def test_species_with_one_sequence_are_not_evaluated():
    species = ["A", "B", "C"]
    d = matrix([[0, 0.1, 0.2], [0.1, 0, 0.3], [0.2, 0.3, 0]])
    assert best_close_match(d, species) == []
    assert summarize_bcm([])["success_rate"] is None


def test_no_competitor_is_excluded():
    species = ["A", "A"]
    d = matrix([[0.0, 0.1], [0.1, 0.0]])
    res = best_close_match(d, species)
    assert {r["reason"] for r in res} == {"no_competitor"}
    assert summarize_bcm(res)["sequences_evaluated"] == 0


def test_nan_distances_are_ignored():
    # B1 has no valid overlap with anything else except B2
    species = ["A", "A", "B", "B"]
    nan = np.nan
    d = matrix([
        [0.0, 0.01, nan, nan],
        [0.01, 0.0, nan, 0.30],
        [nan, nan, 0.0, 0.02],
        [nan, 0.30, 0.02, 0.0],
    ])
    res = best_close_match(d, species)
    assert res[0]["status"] == "excluded"       # A1 has no competitor distance
    assert res[1]["status"] == "success"        # A2: own 0.01 < other 0.30
    assert res[2]["status"] == "excluded"       # B1 has no valid distance to A
    assert res[3]["status"] == "success"


def test_species_distance_matrix_and_nearest_relatives():
    species = ["A", "A", "B", "C"]
    d = matrix([
        [0.0, 0.05, 0.20, 0.50],
        [0.05, 0.0, 0.10, 0.40],
        [0.20, 0.10, 0.0, 0.30],
        [0.50, 0.40, 0.30, 0.0],
    ])
    groups = group_by_species(species)
    sp = species_distance_matrix(d, groups)
    assert groups.names == ["A", "B", "C"]
    assert sp[0, 1] == 0.10  # min over A1-B, A2-B
    assert sp[0, 0] == 0.05  # within-species minimum
    rel = nearest_relatives(sp, groups.names, 2)
    assert rel["A"] == [("B", 0.10), ("C", 0.40)]
    assert rel["C"][0] == ("B", 0.30)


def test_zero_distance_pairs_flags_singletons():
    species = ["A", "B", "C", "C"]
    d = matrix([
        [0.0, 0.0, 0.2, 0.2],   # A (1 seq) identical to B (1 seq)
        [0.0, 0.0, 0.2, 0.2],
        [0.2, 0.2, 0.0, 0.1],
        [0.2, 0.2, 0.1, 0.0],
    ])
    groups = group_by_species(species)
    sp = species_distance_matrix(d, groups)
    pairs = zero_distance_pairs(sp, groups.names, groups.counts)
    assert len(pairs) == 1
    assert (pairs[0]["species_a"], pairs[0]["species_b"]) == ("A", "B")
    assert pairs[0]["involves_singleton"] is True
