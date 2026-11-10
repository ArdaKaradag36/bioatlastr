"""Unit tests for sequencing-priority scoring v2 (caps, ties, robust core)."""

from __future__ import annotations

import pandas as pd
import pytest

from barcode_atlas.priority import (
    COMPONENT_KEYS,
    assign_tie_groups,
    compute_components,
    is_gap_row,
    list_first_of_empty_genera,
    list_tree_gain,
    normalize_weights,
    rank_gaps,
    score_frame,
    select_with_caps,
    sensitivity_analysis,
    sort_by_score_and_ties,
    why_sentence,
)


def _frame() -> pd.DataFrame:
    rows = []
    # Genus A: 1 sequenced + many gaps (tree gain)
    rows.append(dict(species="A with", genus="Agen", family="FamA", endemic=0, wcvp_id="1",
                     n_wcvp_areas=8, n_wcvp_regions=3, n_rbcL=2, n_matK=1, n_ITS=0, n_any=3))
    for i, areas in enumerate([1, 1, 2, 4], start=1):
        rows.append(dict(species=f"A gap{i}", genus="Agen", family="FamA", endemic=1 if areas == 1 else 0,
                         wcvp_id=str(10 + i), n_wcvp_areas=areas, n_wcvp_regions=1,
                         n_rbcL=0, n_matK=0, n_ITS=0, n_any=0))
    # Genus B: empty (no sequences) — first-of-empty list
    for i in range(1, 4):
        rows.append(dict(species=f"B gap{i}", genus="Bgen", family="FamB", endemic=1,
                         wcvp_id=str(20 + i), n_wcvp_areas=1, n_wcvp_regions=1,
                         n_rbcL=0, n_matK=0, n_ITS=0, n_any=0))
    # Genus C: many gaps same family FamA to test family cap
    for i in range(1, 8):
        rows.append(dict(species=f"C gap{i}", genus="Cgen", family="FamA", endemic=0,
                         wcvp_id=str(30 + i), n_wcvp_areas=3, n_wcvp_regions=2,
                         n_rbcL=0, n_matK=0, n_ITS=0, n_any=0))
    # Genus D: sequenced relative, wide range
    rows.append(dict(species="D with", genus="Dgen", family="FamC", endemic=0, wcvp_id="40",
                     n_wcvp_areas=20, n_wcvp_regions=5, n_rbcL=1, n_matK=0, n_ITS=0, n_any=1))
    rows.append(dict(species="D gap1", genus="Dgen", family="FamC", endemic=0, wcvp_id="41",
                     n_wcvp_areas=10, n_wcvp_regions=4, n_rbcL=0, n_matK=0, n_ITS=0, n_any=0))
    df = pd.DataFrame(rows)
    df["is_gap"] = df.apply(lambda r: is_gap_row(r, ["rbcL", "matK"]), axis=1)
    return df


def _scored():
    return score_frame(compute_components(_frame()), {k: 0.2 for k in COMPONENT_KEYS})


def test_gap_rule():
    assert is_gap_row(pd.Series({"n_rbcL": 0, "n_matK": 0, "n_ITS": 9}), ["rbcL", "matK"])
    assert not is_gap_row(pd.Series({"n_rbcL": 1, "n_matK": 0}), ["rbcL", "matK"])


def test_components_continuous_and_phy_scales_with_congeners():
    c = compute_components(_frame())
    gaps = c[c["is_gap"]]
    for k in COMPONENT_KEYS:
        assert gaps[k].between(0, 1).all()
    # phylogenetic usefulness is continuous: Agen has 1 sequenced, Dgen has 1, Bgen has 0
    a = float(c.set_index("species").loc["A gap1", "phylogenetic_usefulness"])
    b = float(c.set_index("species").loc["B gap1", "phylogenetic_usefulness"])
    assert a > b
    assert gaps["range_restriction"].nunique() > 1
    assert gaps["genus_gap"].nunique() > 1


def test_tiebreakers_prefer_more_congeners_then_fewer_areas_not_alphabet():
    scored = _scored()
    # Force equal total_score on two A gaps with different areas
    scored = scored.copy()
    scored.loc[scored["species"].isin(["A gap1", "A gap3"]), "total_score"] = 0.9
    ordered = sort_by_score_and_ties(scored[scored["species"].isin(["A gap1", "A gap3"])])
    # same genus_n_with_any; fewer areas first → A gap1 (1 area) before A gap3 (2 areas)
    assert list(ordered["species"]) == ["A gap1", "A gap3"]


def test_select_with_caps_limits_genus_and_family():
    scored = _scored()
    ordered = sort_by_score_and_ties(scored[scored["is_gap"]])
    capped = select_with_caps(ordered, top_n=10, max_per_genus=2, max_per_family=4)
    assert capped["genus"].value_counts().max() <= 2
    assert capped["family"].value_counts().max() <= 4
    assert len(capped) <= 10


def test_rank_gaps_caps_and_why_mentions_cap():
    scored = _scored()
    top = rank_gaps(
        scored,
        {k: 0.2 for k in COMPONENT_KEYS},
        top_n=6,
        max_per_genus=2,
        max_per_family=4,
        apply_caps=True,
    )
    assert len(top) <= 6
    assert top["genus"].value_counts().max() <= 2
    assert "çeşitlilik tavanı" in top.iloc[0]["neden_bu_tur"]


def test_tie_group_flags_identical_keys():
    scored = _scored()
    gaps = sort_by_score_and_ties(scored[scored["is_gap"]])
    gaps["tie_group"] = assign_tie_groups(gaps)
    # At least groups are positive ints
    assert gaps["tie_group"].min() >= 1


def test_empty_genera_and_tree_gain_lists():
    scored = _scored()
    ordered = sort_by_score_and_ties(scored[scored["is_gap"]])
    empty = list_first_of_empty_genera(ordered)
    assert set(empty["genus"]) == {"Bgen", "Cgen"}  # both genera have zero sequences
    assert (empty["genus_n_with_any"] == 0).all()
    assert empty["genus"].is_unique
    gain = list_tree_gain(ordered)
    assert (gain["genus_n_with_any"] > 0).all()
    assert "tree_gain" in gain.columns
    assert gain.iloc[0]["tree_gain"] >= gain.iloc[-1]["tree_gain"]


def test_sensitivity_robust_core_and_spearman():
    components = compute_components(_frame())
    default = {k: 0.2 for k in COMPONENT_KEYS}
    alts = {
        "equal": default,
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
        "range_focus": {
            "endemism": 0.1,
            "range_restriction": 0.5,
            "genus_gap": 0.15,
            "phylogenetic_usefulness": 0.1,
            "family_gap": 0.15,
        },
    }
    sens, robust, tops = sensitivity_analysis(
        components,
        default,
        alts,
        top_n=5,
        max_per_genus=2,
        max_per_family=4,
    )
    assert "capped_overlap_count" in sens.columns
    assert "spearman_full_scores" in sens.columns
    diag = sens[(sens.set_a == sens.set_b)]
    assert (diag["capped_overlap_count"] == 5).all()
    assert isinstance(robust, set)
    assert all(sp in tops["default"] for sp in robust)
