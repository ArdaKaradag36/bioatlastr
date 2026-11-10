"""Tests for Wilson intervals and paired marker comparisons."""

from __future__ import annotations

import pytest

from barcode_atlas.marker_guide import (
    apply_holm_to_pairs,
    holm_adjust,
    intervals_overlap,
    mcnemar_exact_p,
    pair_sentence,
    paired_compare,
    share_label,
    summarize_family_fixed,
    wilson_interval,
)


def test_wilson_known_values():
    # n=100, k=50 → ~0.5 with symmetric-ish CI
    p, lo, hi = wilson_interval(50, 100)
    assert p == pytest.approx(0.5)
    assert lo is not None and hi is not None
    assert lo < 0.5 < hi
    assert lo == pytest.approx(0.4038, abs=0.002)
    assert hi == pytest.approx(0.5962, abs=0.002)
    # extremes
    p0, lo0, hi0 = wilson_interval(0, 20)
    assert p0 == 0.0 and lo0 == 0.0 and hi0 is not None and hi0 > 0
    p1, lo1, hi1 = wilson_interval(20, 20)
    assert p1 == 1.0 and hi1 == 1.0 and lo1 is not None and lo1 < 1
    assert wilson_interval(0, 0) == (None, None, None)


def test_wilson_monotonic_in_k():
    lows = [wilson_interval(k, 40)[1] for k in range(0, 41)]
    assert all(lows[i] <= lows[i + 1] + 1e-12 for i in range(len(lows) - 1))


def test_mcnemar_symmetric_and_extremes():
    assert mcnemar_exact_p(5, 5) == pytest.approx(1.0)
    assert mcnemar_exact_p(0, 0) == 1.0
    # strongly one-sided
    assert mcnemar_exact_p(0, 10) < 0.01
    assert mcnemar_exact_p(10, 0) < 0.01


def test_intervals_overlap():
    assert intervals_overlap(0.1, 0.3, 0.25, 0.4)
    assert not intervals_overlap(0.1, 0.2, 0.3, 0.4)


def test_holm_adjust_known():
    # classic: two p=0.04, 0.04 → both adjusted to 0.08
    adj = holm_adjust([0.04, 0.04])
    assert adj[0] == pytest.approx(0.08)
    assert adj[1] == pytest.approx(0.08)
    # monotonic non-decreasing in sorted order
    raw = [0.01, 0.04, 0.03, 0.20]
    adj2 = holm_adjust(raw)
    ordered = [adj2[i] for i in sorted(range(len(raw)), key=lambda i: raw[i])]
    assert all(ordered[i] <= ordered[i + 1] + 1e-12 for i in range(len(ordered) - 1))
    assert all(a >= p - 1e-12 for a, p in zip(adj2, raw))


def test_paired_compare_insufficient_n():
    # 10 shared species, A better on all
    st = {f"s{i}": {"rbcL": 0, "ITS": 1} for i in range(10)}
    out = paired_compare(st, "rbcL", "ITS", min_shared=15, z=1.96, alpha=0.05)
    assert out["n_shared"] == 10
    assert out["recommendation"] == "yetersiz veri"
    assert out["clear_difference"] is False


def test_paired_compare_clear_winner_large_n():
    # 40 species: ITS succeeds for all, rbcL for none → strong McNemar
    st = {f"s{i}": {"rbcL": 0, "ITS": 1} for i in range(40)}
    out = paired_compare(st, "rbcL", "ITS", min_shared=15, z=1.96, alpha=0.05)
    assert out["n_shared"] == 40
    assert out["success_a"] == 0 and out["success_b"] == 40
    assert out["ci_overlap"] is False
    assert out["recommendation"] == "ITS"
    assert out["clear_difference"] is True
    assert out["mcnemar_p"] is not None and out["mcnemar_p"] < 0.05


def test_paired_compare_unclear_when_similar():
    # 30 species, almost tied
    st = {}
    for i in range(15):
        st[f"a{i}"] = {"rbcL": 1, "matK": 1}
    for i in range(15):
        st[f"b{i}"] = {"rbcL": 0, "matK": 0}
    out = paired_compare(st, "rbcL", "matK", min_shared=15, z=1.96, alpha=0.05)
    assert out["n_shared"] == 30
    assert out["recommendation"] == "fark belirsiz"
    assert out["ci_overlap"] is True


def test_holm_downgrades_borderline_among_many_tests():
    """A raw-significant but weak pair becomes 'fark belirsiz' after Holm among many tests."""
    # Strong pair: 40 discordance all one way
    strong = paired_compare(
        {f"s{i}": {"rbcL": 0, "ITS": 1} for i in range(40)},
        "rbcL", "ITS", min_shared=15, z=1.96, alpha=0.05,
    )
    # Borderline: 6 of 20 discordant favoring matK (exact p = 0.03125)
    weak_st = {}
    for i in range(14):
        weak_st[f"t{i}"] = {"rbcL": 1, "matK": 1}
    for i in range(6):
        weak_st[f"w{i}"] = {"rbcL": 0, "matK": 1}
    weak = paired_compare(weak_st, "rbcL", "matK", min_shared=15, z=1.96, alpha=0.05)
    assert weak["recommendation"] == "matK"
    assert weak["mcnemar_p"] is not None and weak["mcnemar_p"] < 0.05

    rows = []
    for tag, cmp, fam in (("strong", strong, "FamA"), ("weak", weak, "FamB")):
        rows.append({
            "scope_level": "family",
            "scope_name": fam,
            "family": fam,
            "genus": "",
            "n_family_species": 1000,
            **cmp,
        })
    # Pad with many non-significant adequate tests so Holm inflates the weak p
    for i in range(20):
        tied = paired_compare(
            {f"x{j}": {"rbcL": 1, "matK": 1} for j in range(20)},
            "rbcL", "matK", min_shared=15, z=1.96, alpha=0.05,
        )
        rows.append({
            "scope_level": "family",
            "scope_name": f"Pad{i}",
            "family": f"Pad{i}",
            "genus": "",
            "n_family_species": 100,
            **tied,
        })
    apply_holm_to_pairs(rows, min_shared=15, alpha=0.05)
    by_fam = {r["family"]: r for r in rows}
    assert by_fam["FamA"]["recommendation"] == "ITS"
    assert by_fam["FamA"]["clear_difference"] is True
    assert by_fam["FamB"]["recommendation"] == "fark belirsiz"
    assert by_fam["FamB"]["clear_difference"] is False
    assert by_fam["FamB"]["mcnemar_p_holm"] is not None
    assert by_fam["FamB"]["mcnemar_p_holm"] >= 0.05


def test_share_label_and_sentence_include_family_total():
    assert share_label(34, 1297) == "34 / 1.297 tür"
    row = {
        "marker_a": "rbcL",
        "marker_b": "ITS",
        "n_shared": 34,
        "n_family_species": 1297,
        "rate_a": 0.176,
        "rate_b": 0.794,
        "wilson_a_low": 0.08,
        "wilson_a_high": 0.33,
        "wilson_b_low": 0.63,
        "wilson_b_high": 0.90,
        "recommendation": "ITS",
    }
    s = pair_sentence("Asteraceae", row)
    assert "34 / 1.297 tür" in s
    assert "Holm" in s


def test_family_pair_vote_no_double_species_and_tie():
    """Çift oylaması: family-level clear pairs vote; ties → fark belirsiz."""
    def _clear(rec: str, n: int, diff: float) -> dict:
        return {
            "scope_level": "family",
            "family": "Demo",
            "recommendation": rec,
            "clear_difference": True,
            "n_shared": n,
            "n_family_species": 200,
            "rate_diff_b_minus_a": diff,
            "sentence": f"winner {rec} n={n}",
        }

    # one vote each → tie
    rows = [
        _clear("matK", 40, 0.3),
        {**_clear("ITS", 34, 0.4), "clear_difference": True},
        {
            "scope_level": "family",
            "family": "Demo",
            "recommendation": "yetersiz veri",
            "clear_difference": False,
            "n_shared": 5,
            "n_family_species": 200,
            "rate_diff_b_minus_a": 0.0,
            "sentence": "skip",
        },
        # genus row must not affect family summary
        {
            "scope_level": "genus",
            "family": "Demo",
            "genus": "G",
            "recommendation": "rbcL",
            "clear_difference": True,
            "n_shared": 50,
            "n_family_species": 200,
            "rate_diff_b_minus_a": 0.9,
            "sentence": "genus should not vote",
        },
    ]
    out = summarize_family_fixed(rows, "Demo", n_family_species=200)
    assert out["recommendation"] == "fark belirsiz"
    assert "200" in out["sentence"] or "200" in share_label(40, 200)
