"""Tests for Wilson intervals and paired marker comparisons."""

from __future__ import annotations

import math

import pytest

from barcode_atlas.marker_guide import (
    intervals_overlap,
    mcnemar_exact_p,
    paired_compare,
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


def test_paired_compare_insufficient_n():
    # 10 shared species, A better on all
    st = {f"s{i}": {"rbcL": 0, "ITS": 1} for i in range(10)}
    out = paired_compare(st, "rbcL", "ITS", min_shared=15, z=1.96, alpha=0.05)
    assert out["n_shared"] == 10
    assert out["recommendation"] == "yetersiz veri"
    assert out["clear_difference"] is False


def test_paired_compare_clear_winner_large_n():
    # 40 species: ITS succeeds for all, rbcL for none → non-overlapping CIs
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
