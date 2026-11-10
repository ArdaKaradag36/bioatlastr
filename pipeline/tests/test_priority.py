"""Unit tests for sequencing-priority scoring (synthetic tables; no network)."""

from __future__ import annotations

import pandas as pd
import pytest

from barcode_atlas.priority import (
    COMPONENT_KEYS,
    compute_components,
    is_gap_row,
    normalize_weights,
    rank_gaps,
    score_frame,
    sensitivity_table,
    why_sentence,
)


def _tiny_frame() -> pd.DataFrame:
    # Two genera in one family; markers chosen so gaps are clear.
    return pd.DataFrame([
        # Genus A: 3 species, only A-with has data → gaps get phylogenetic_usefulness=1
        dict(species="A alpha", genus="Agen", family="Fam", endemic=1, n_wcvp_areas=1,
             n_rbcL=0, n_matK=0, n_ITS=0, n_any=0),
        dict(species="A beta", genus="Agen", family="Fam", endemic=0, n_wcvp_areas=4,
             n_rbcL=0, n_matK=0, n_ITS=0, n_any=0),
        dict(species="A with", genus="Agen", family="Fam", endemic=0, n_wcvp_areas=10,
             n_rbcL=2, n_matK=1, n_ITS=0, n_any=3),
        # Genus B: all gaps (zero data in genus) → phylogenetic_usefulness=0, genus_gap=1
        dict(species="B one", genus="Bgen", family="Fam", endemic=1, n_wcvp_areas=1,
             n_rbcL=0, n_matK=0, n_ITS=0, n_any=0),
        dict(species="B two", genus="Bgen", family="Fam", endemic=0, n_wcvp_areas=2,
             n_rbcL=0, n_matK=0, n_ITS=0, n_any=0),  # whole genus has zero sequences
        # ITS-only species: still a gap under the default rbcL+matK rule
        dict(species="C itsonly", genus="Cgen", family="Fam", endemic=0, n_wcvp_areas=3,
             n_rbcL=0, n_matK=0, n_ITS=4, n_any=4),
    ])


def test_gap_rule_requires_all_listed_markers_empty():
    row = pd.Series({"n_rbcL": 0, "n_matK": 0, "n_ITS": 9})
    assert is_gap_row(row, ["rbcL", "matK"]) is True
    assert is_gap_row(row, ["rbcL", "matK", "ITS"]) is False
    assert is_gap_row(pd.Series({"n_rbcL": 1, "n_matK": 0}), ["rbcL", "matK"]) is False


def test_components_are_unit_interval_and_match_definitions():
    raw = _tiny_frame()
    raw["is_gap"] = raw.apply(lambda r: is_gap_row(r, ["rbcL", "matK"]), axis=1)
    c = compute_components(raw)
    assert set(COMPONENT_KEYS).issubset(c.columns)
    for k in COMPONENT_KEYS:
        assert c[k].between(0, 1).all()
    alpha = c.set_index("species").loc["A alpha"]
    assert alpha["endemism"] == 1.0
    assert alpha["range_restriction"] == pytest.approx(1.0)
    assert alpha["genus_gap"] == pytest.approx(2 / 3)  # A alpha, A beta gaps; A with not
    assert alpha["phylogenetic_usefulness"] == 1.0
    b_one = c.set_index("species").loc["B one"]
    assert b_one["genus_gap"] == pytest.approx(1.0)
    assert b_one["phylogenetic_usefulness"] == 0.0
    its = c.set_index("species").loc["C itsonly"]
    assert its["is_gap"] is True or bool(its["is_gap"]) is True
    # Family: A alpha,A beta,B one,B two,C itsonly = 5 gaps; A with has data → 5/6
    assert alpha["family_gap"] == pytest.approx(5 / 6)


def test_ranking_prefers_endemic_narrow_range_when_weights_say_so():
    raw = _tiny_frame()
    raw["is_gap"] = raw.apply(lambda r: is_gap_row(r, ["rbcL", "matK"]), axis=1)
    c = compute_components(raw)
    weights = {
        "endemism": 0.5,
        "range_restriction": 0.3,
        "genus_gap": 0.1,
        "phylogenetic_usefulness": 0.05,
        "family_gap": 0.05,
    }
    ranked = rank_gaps(score_frame(c, weights), weights)
    assert list(ranked["species"])[0] in {"A alpha", "B one"}  # both endemic, 1 area
    assert "A with" not in set(ranked["species"])  # not a gap
    assert ranked["rank"].tolist() == list(range(1, len(ranked) + 1))


def test_why_sentence_mentions_driving_components():
    raw = _tiny_frame()
    raw["is_gap"] = True
    c = compute_components(raw)
    row = c.set_index("species").loc["A alpha"]
    weights = normalize_weights({
        "endemism": 0.4,
        "range_restriction": 0.3,
        "genus_gap": 0.1,
        "phylogenetic_usefulness": 0.1,
        "family_gap": 0.1,
    })
    text = why_sentence(row, weights)
    assert "Öncelikli çünkü" in text
    assert "endemiği" in text or "endemik" in text.lower() or "Türkiye endemiği" in text


def test_sensitivity_overlap_is_stable_on_tiny_set():
    raw = _tiny_frame()
    raw["is_gap"] = raw.apply(lambda r: is_gap_row(r, ["rbcL", "matK"]), axis=1)
    c = compute_components(raw)
    default = {
        "endemism": 0.3,
        "range_restriction": 0.2,
        "genus_gap": 0.2,
        "phylogenetic_usefulness": 0.15,
        "family_gap": 0.15,
    }
    alts = {
        "equal": {k: 0.2 for k in COMPONENT_KEYS},
        "endemism_focus": {
            "endemism": 0.5,
            "range_restriction": 0.2,
            "genus_gap": 0.1,
            "phylogenetic_usefulness": 0.1,
            "family_gap": 0.1,
        },
        "coverage_focus": {
            "endemism": 0.1,
            "range_restriction": 0.1,
            "genus_gap": 0.35,
            "phylogenetic_usefulness": 0.2,
            "family_gap": 0.25,
        },
    }
    sens = sensitivity_table(c, default, alts, top_n=3)
    diag = sens[(sens.set_a == sens.set_b)]
    assert (diag["overlap_count"] == 3).all()
    # equal vs default should share most of a 3-species top list on this toy set
    pair = sens[(sens.set_a == "default") & (sens.set_b == "equal")].iloc[0]
    assert pair["overlap_count"] >= 2
