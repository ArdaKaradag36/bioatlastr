"""p-distances from an alignment and a fast neighbor-joining tree builder.

Biopython's own `DistanceTreeConstructor.nj` is pure Python and cubic, which is
too slow for families with thousands of sequences. We therefore run the NJ
algorithm with numpy and still use Biopython's `Phylo` classes for the tree
object and the Newick output. Tests compare our NJ to Biopython's on small data.
"""

from __future__ import annotations

import io
import sys

import numpy as np
from Bio import Phylo
from Bio.Phylo.BaseTree import Clade, Tree

# Newick writing of very unbalanced trees is recursive.
sys.setrecursionlimit(20000)

_CODES = np.full(256, -1, dtype=np.int8)
for _i, _c in enumerate("ACGT"):
    _CODES[ord(_c)] = _i


def encode_alignment(aligned: list[str]) -> np.ndarray:
    """Aligned strings -> int8 matrix (A,C,G,T = 0..3; gaps and ambiguity codes = -1)."""
    width = len(aligned[0])
    mat = np.empty((len(aligned), width), dtype=np.int8)
    for i, s in enumerate(aligned):
        mat[i] = _CODES[np.frombuffer(s.upper().encode("ascii"), dtype=np.uint8)]
    return mat


def p_distance_matrix(codes: np.ndarray, min_overlap: int = 1) -> np.ndarray:
    """Pairwise p-distance (mismatches / compared sites), gaps and ambiguities ignored.

    Pairs sharing fewer than `min_overlap` comparable sites get NaN (no reliable value).
    """
    n = codes.shape[0]
    dist = np.zeros((n, n), dtype=np.float32)
    valid = codes >= 0
    for i in range(n - 1):
        rest = slice(i + 1, n)
        both = valid[rest] & valid[i]
        overlap = both.sum(axis=1)
        mism = ((codes[rest] != codes[i]) & both).sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            d = np.where(overlap >= max(min_overlap, 1), mism / np.maximum(overlap, 1), np.nan)
        dist[i, rest] = d
        dist[rest, i] = d
    return dist


# ---------------------------------------------------------------------------
# Neighbor joining
# ---------------------------------------------------------------------------
def fill_missing(dist: np.ndarray) -> np.ndarray:
    """Replace NaN (too little overlap) by the largest observed distance (or 1)."""
    out = dist.astype(np.float64).copy()
    finite = out[np.isfinite(out)]
    out[~np.isfinite(out)] = finite.max() if finite.size else 1.0
    np.fill_diagonal(out, 0.0)
    return out


def neighbor_joining_edges(dist: np.ndarray) -> tuple[list[tuple[int, int, float]], int]:
    """Classic NJ. Returns (edges, n_nodes); leaves are 0..n-1, inner nodes follow.

    Edges are (node_a, node_b, length). Negative lengths are clipped to 0.
    """
    d = dist.astype(np.float64).copy()
    n = d.shape[0]
    if n < 2:
        raise ValueError("Need at least 2 sequences")
    if n == 2:
        return [(0, 1, float(d[0, 1]))], 2

    nodes = list(range(n))  # node id for every active row
    edges: list[tuple[int, int, float]] = []
    next_id = n
    active = n
    while active > 3:
        rows = d[:active, :active]
        r = rows.sum(axis=1)
        q = (active - 2) * rows - r[:, None] - r[None, :]
        np.fill_diagonal(q, np.inf)
        i, j = np.unravel_index(np.argmin(q), q.shape)
        if i > j:
            i, j = j, i
        dij = rows[i, j]
        li = 0.5 * dij + (r[i] - r[j]) / (2.0 * (active - 2))
        lj = dij - li
        u = next_id
        next_id += 1
        edges.append((nodes[i], u, max(float(li), 0.0)))
        edges.append((nodes[j], u, max(float(lj), 0.0)))
        # distances from the new node to every other active node
        new_row = 0.5 * (rows[i, :] + rows[j, :] - dij)
        # put the new node in slot i, move the last active row into slot j
        d[i, :active] = new_row
        d[:active, i] = new_row
        d[i, i] = 0.0
        last = active - 1
        if j != last:
            d[j, :active] = d[last, :active]
            d[:active, j] = d[:active, last]
            d[j, j] = 0.0
            nodes[j] = nodes[last]
        nodes[i] = u
        active -= 1

    # three nodes left: join them in a star around a final inner node
    a, b, c = 0, 1, 2
    u = next_id
    la = 0.5 * (d[a, b] + d[a, c] - d[b, c])
    lb = 0.5 * (d[a, b] + d[b, c] - d[a, c])
    lc = 0.5 * (d[a, c] + d[b, c] - d[a, b])
    for idx, length in ((a, la), (b, lb), (c, lc)):
        edges.append((nodes[idx], u, max(float(length), 0.0)))
    return edges, u + 1


def _midpoint_root(edges: list[tuple[int, int, float]], n_nodes: int, n_leaves: int):
    """Return (root_id, children_map, length_map) after midpoint rooting. Iterative, O(n)."""
    adj: dict[int, list[tuple[int, float]]] = {i: [] for i in range(n_nodes)}
    for a, b, w in edges:
        adj[a].append((b, w))
        adj[b].append((a, w))

    def farthest(start: int):
        dist = {start: 0.0}
        parent = {start: None}
        stack = [start]
        while stack:
            x = stack.pop()
            for y, w in adj[x]:
                if y not in dist:
                    dist[y] = dist[x] + w
                    parent[y] = x
                    stack.append(y)
        far = max((k for k in dist if k < n_leaves), key=lambda k: dist[k])
        return far, dist, parent

    a, _, _ = farthest(0)
    b, dist_a, parent = farthest(a)  # distances measured from leaf a
    half = dist_a[b] / 2.0

    # walk from b towards a until we pass the midpoint
    node = b
    while parent[node] is not None and dist_a[parent[node]] > half:
        node = parent[node]
    par = parent[node]
    if par is None:  # degenerate: all distances zero
        par = node
    edge_len = dist_a[node] - dist_a[par] if par != node else 0.0
    root = n_nodes
    # split the edge (par,node) with the new root
    new_adj = {k: list(v) for k, v in adj.items()}
    new_adj[root] = []
    if par != node:
        new_adj[par] = [(y, w) for y, w in new_adj[par] if y != node]
        new_adj[node] = [(y, w) for y, w in new_adj[node] if y != par]
        to_node = max(dist_a[node] - half, 0.0)
        new_adj[root] = [(node, to_node), (par, max(edge_len - to_node, 0.0))]
        new_adj[node].append((root, to_node))
        new_adj[par].append((root, max(edge_len - to_node, 0.0)))
    else:
        new_adj[root] = [(y, w) for y, w in adj[node]]
    return root, new_adj


def build_tree(dist: np.ndarray, names: list[str]) -> Tree:
    """NJ tree (midpoint rooted) as a Biopython Tree with leaf names `names`."""
    filled = fill_missing(dist)
    n = len(names)
    edges, n_nodes = neighbor_joining_edges(filled)
    if n == 2:
        left = Clade(branch_length=edges[0][2] / 2, name=names[0])
        right = Clade(branch_length=edges[0][2] / 2, name=names[1])
        return Tree(root=Clade(clades=[left, right]), rooted=True)

    root, adj = _midpoint_root(edges, n_nodes, n)
    clades: dict[int, Clade] = {}
    parent_of: dict[int, int | None] = {root: None}
    order: list[int] = []
    stack = [root]
    while stack:  # iterative DFS (trees can be very deep)
        x = stack.pop()
        order.append(x)
        for y, _ in adj[x]:
            if y not in parent_of:
                parent_of[y] = x
                stack.append(y)
    length_of = {}
    for x in order:
        for y, w in adj[x]:
            if parent_of.get(y) == x:
                length_of[y] = w
    for x in reversed(order):
        clade = Clade(branch_length=length_of.get(x), name=names[x] if x < n else None)
        clades[x] = clade
    for x in order:
        p = parent_of[x]
        if p is not None:
            clades[p].clades.append(clades[x])
    return Tree(root=clades[root], rooted=True)


def tree_to_newick(tree: Tree) -> str:
    buf = io.StringIO()
    Phylo.write(tree, buf, "newick", branch_length_only=False, format_branch_length="%.6f")
    return buf.getvalue().strip()
