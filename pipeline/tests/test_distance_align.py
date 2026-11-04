"""Tests for p-distance, NJ trees and the fallback aligner."""

import numpy as np
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceMatrix, DistanceTreeConstructor

from barcode_atlas.align import align_fallback
from barcode_atlas.distance import build_tree, encode_alignment, p_distance_matrix, tree_to_newick


def test_p_distance_ignores_gaps_and_n():
    aligned = ["ACGTACGTAC", "ACGTACGTAA", "AC--ACGTNC"]
    d = p_distance_matrix(encode_alignment(aligned))
    assert d[0, 1] == 0.1                       # 1 mismatch in 10 sites
    assert abs(d[0, 2] - 0.0) < 1e-9            # only 7 comparable sites, all equal
    assert d[0, 0] == 0.0 and d[1, 0] == d[0, 1]  # symmetric


def test_p_distance_min_overlap_gives_nan():
    aligned = ["ACGTAC----", "----ACGTAC"]  # only 2 shared sites
    d = p_distance_matrix(encode_alignment(aligned), min_overlap=5)
    assert np.isnan(d[0, 1])


def test_nj_matches_biopython_on_random_data():
    rng = np.random.default_rng(1)
    n = 9
    # additive-ish random distances from random points -> unique NJ tree
    pts = rng.random((n, 4))
    d = np.linalg.norm(pts[:, None] - pts[None], axis=2)
    names = [f"t{i}" for i in range(n)]

    ours = build_tree(d, names)
    lower = [list(d[i, : i + 1]) for i in range(n)]
    bio = DistanceTreeConstructor().nj(DistanceMatrix(names, lower))

    # Compare leaf-to-leaf path lengths (independent of where the tree is rooted).
    for i in range(n):
        for j in range(i + 1, n):
            a = ours.distance(names[i], names[j])
            b = bio.distance(names[i], names[j])
            assert abs(a - b) < 1e-6, (names[i], names[j], a, b)


def test_newick_roundtrip_has_all_leaves():
    d = np.array([[0, 0.1, 0.4, 0.5], [0.1, 0, 0.45, 0.5], [0.4, 0.45, 0, 0.2], [0.5, 0.5, 0.2, 0]])
    names = ["a__1", "b__2", "c__3", "d__4"]
    newick = tree_to_newick(build_tree(d, names))
    assert newick.endswith(";")
    from io import StringIO
    tree = Phylo.read(StringIO(newick), "newick")
    assert sorted(t.name for t in tree.get_terminals()) == names


def test_two_and_identical_sequences_trees():
    names = ["x", "y"]
    t = build_tree(np.array([[0, 0.2], [0.2, 0]]), names)
    assert len(t.get_terminals()) == 2
    same = np.zeros((4, 4))
    t4 = build_tree(same, ["a", "b", "c", "d"])
    assert len(t4.get_terminals()) == 4


def test_deep_tree_does_not_crash():
    # a long "caterpillar" tree exercises iterative construction
    n = 400
    d = np.abs(np.arange(n)[:, None] - np.arange(n)[None]).astype(float)
    tree = build_tree(d, [f"s{i}" for i in range(n)])
    assert len(tree.get_terminals()) == n
    assert tree_to_newick(tree).count("s") >= n


def test_fallback_alignment_keeps_sequences():
    base = "ATGCGTACGTTAGCTAGCTAGGATCCGATCGATCGTAGCTAGCTAGGCTAAGCTT"
    seqs = {
        "a": base,
        "b": base[:20] + base[23:],                 # 3 bp deletion
        "c": base[:30] + "GGG" + base[30:],         # 3 bp insertion
        "d": base[5:-5],                            # shorter at both ends
    }
    aligned = align_fallback(seqs)
    lengths = {len(v) for v in aligned.values()}
    assert len(lengths) == 1                         # all rows equal length
    for key, row in aligned.items():
        assert row.replace("-", "") == seqs[key]     # residues are unchanged


def test_fallback_alignment_handles_reverse_complement():
    base = "ATGCGTACGTTAGCTAGCTAGGATCCGATCGATCGTAGCTAGCTAGGCTAAGCTT"
    rc = base[::-1].translate(str.maketrans("ACGT", "TGCA"))
    aligned = align_fallback({"fwd": base, "rev": rc})
    d = p_distance_matrix(encode_alignment(list(aligned.values())))
    assert d[0, 1] == 0.0
