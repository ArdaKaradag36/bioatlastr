"""Barcode discrimination metrics computed from a distance matrix.

All functions take a square distance matrix `dist` (numpy, NaN = unknown) and a
list `species` with one species name per row. They are pure functions, so they
are easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

EPS = 1e-9  # distances closer than this are treated as equal (ties)


@dataclass
class SpeciesGroups:
    """Rows sorted by species so we can use fast grouped minima."""

    order: np.ndarray        # row indices sorted by species
    starts: np.ndarray       # first position of each species in the sorted order
    names: list[str]         # species names (same order as `starts`)
    species_of_row: np.ndarray  # original row -> species group index
    counts: np.ndarray       # number of sequences per species group


def group_by_species(species: list[str]) -> SpeciesGroups:
    names = sorted(set(species))
    index = {s: i for i, s in enumerate(names)}
    row_group = np.array([index[s] for s in species])
    order = np.argsort(row_group, kind="stable")
    counts = np.bincount(row_group, minlength=len(names))
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(int)
    return SpeciesGroups(order, starts, names, row_group, counts)


def _inf_matrix(dist: np.ndarray) -> np.ndarray:
    d = dist.astype(np.float64).copy()
    d[~np.isfinite(d)] = np.inf
    return d


def species_distance_matrix(dist: np.ndarray, groups: SpeciesGroups) -> np.ndarray:
    """k x k matrix: smallest distance between any sequence of species a and any of species b.

    Diagonal = smallest distance between two different sequences of the same species
    (inf when the species has a single sequence).
    """
    d = _inf_matrix(dist)
    np.fill_diagonal(d, np.inf)  # a sequence is never compared with itself
    d = d[groups.order][:, groups.order]
    rows = np.minimum.reduceat(d, groups.starts, axis=0)
    return np.minimum.reduceat(rows, groups.starts, axis=1)


def best_close_match(dist: np.ndarray, species: list[str]) -> list[dict]:
    """"Best close match" test (Meier et al. 2006) for sequences of species with 2+ sequences.

    For each sequence we look for its nearest neighbour (smallest p-distance, itself excluded):
      success   - the nearest neighbour(s) are all the same species
      ambiguous - the nearest distance is shared by the same species AND another species (tie)
      fail      - the nearest neighbour belongs to another species
    Sequences that cannot be judged are reported with the status 'excluded' and a reason:
      no_competitor      - no other species with data in this comparison set
      no_conspecific     - no valid distance to another sequence of the same species
    """
    groups = group_by_species(species)
    d = _inf_matrix(dist)
    np.fill_diagonal(d, np.inf)
    # per sequence: smallest distance to each species -> n x k
    per_species_min = np.minimum.reduceat(d[:, groups.order], groups.starts, axis=1)

    out: list[dict] = []
    for i, sp in enumerate(species):
        g = groups.species_of_row[i]
        if groups.counts[g] < 2:
            continue  # only species with 2+ sequences are evaluated
        own = per_species_min[i, g]
        others_row = per_species_min[i].copy()
        others_row[g] = np.inf
        others = others_row.min()
        if np.isinf(others):
            status, reason = "excluded", "no_competitor"
        elif np.isinf(own):
            status, reason = "excluded", "no_conspecific"
        elif abs(own - others) <= EPS:
            status, reason = "ambiguous", ""
        elif own < others:
            status, reason = "success", ""
        else:
            status, reason = "fail", ""
        nearest_other = groups.names[int(np.argmin(others_row))] if not np.isinf(others) else ""
        out.append({
            "row": i,
            "species": sp,
            "status": status,
            "reason": reason,
            "nearest_conspecific": None if np.isinf(own) else float(own),
            "nearest_other": None if np.isinf(others) else float(others),
            "nearest_other_species": nearest_other,
        })
    return out


def summarize_bcm(results: list[dict]) -> dict:
    """Counts and success rates from best_close_match() output (sequence and species level)."""
    evaluated = [r for r in results if r["status"] != "excluded"]
    n = len(evaluated)
    counts = {s: sum(1 for r in evaluated if r["status"] == s) for s in ("success", "ambiguous", "fail")}

    # species level: a species is discriminated only if ALL its evaluated sequences succeed
    by_species: dict[str, list[str]] = {}
    for r in evaluated:
        by_species.setdefault(r["species"], []).append(r["status"])
    species_status = {sp: species_status_from(statuses) for sp, statuses in by_species.items()}
    n_sp = len(species_status)
    n_sp_success = sum(1 for s in species_status.values() if s == "success")
    return {
        "sequences_evaluated": n,
        "sequences_excluded": len(results) - n,
        "success": counts["success"],
        "ambiguous": counts["ambiguous"],
        "fail": counts["fail"],
        "success_rate": counts["success"] / n if n else None,
        "species_evaluated": n_sp,
        "species_success": n_sp_success,
        "species_success_rate": n_sp_success / n_sp if n_sp else None,
    }


def species_status_from(statuses: list[str]) -> str:
    """Combine sequence-level statuses of one species into one status."""
    if all(s == "success" for s in statuses):
        return "success"
    if any(s == "fail" for s in statuses):
        return "fail"
    return "ambiguous"


def nearest_relatives(sp_dist: np.ndarray, names: list[str], k: int) -> dict[str, list[tuple[str, float]]]:
    """For each species the k closest other species (name, distance), closest first."""
    out: dict[str, list[tuple[str, float]]] = {}
    for i, name in enumerate(names):
        row = sp_dist[i].copy()
        row[i] = np.inf
        order = np.argsort(row, kind="stable")
        out[name] = [(names[j], float(row[j])) for j in order[:k] if np.isfinite(row[j])]
    return out


def zero_distance_pairs(sp_dist: np.ndarray, names: list[str], counts: np.ndarray) -> list[dict]:
    """Species pairs whose smallest distance is 0 (identical barcode sequence in this marker).

    `min_sequences` is the smaller number of sequences of the two species; when it is 1 the
    pair involves a species known from a single sequence (so we cannot tell if it is only
    that individual which is identical).
    """
    pairs = []
    # upper triangle only, so every pair is listed once
    for i, j in np.argwhere(np.triu(sp_dist <= EPS, k=1)):
        smaller = int(min(counts[i], counts[j]))
        pairs.append({
            "species_a": names[i],
            "species_b": names[j],
            "sequences_a": int(counts[i]),
            "sequences_b": int(counts[j]),
            "min_sequences": smaller,
            "involves_singleton": smaller == 1,
        })
    return pairs


def combined_species_distance(mats: dict, combo: list[str]):
    """Species x species distance for one marker or a marker combination.

    mats: {marker: (species names, species distance matrix from species_distance_matrix())}
    Every marker contributes where BOTH species have data; the result is the mean over those
    markers. The diagonal is the smallest distance between two sequences of the same species.
    Returns (names, matrix) with NaN where nothing can be compared.
    """
    names = sorted(set().union(*(set(mats[m][0]) for m in combo)))
    idx = {n: i for i, n in enumerate(names)}
    k = len(names)
    total = np.zeros((k, k))
    count = np.zeros((k, k))
    for m in combo:
        mnames, sd = mats[m]
        ix = np.array([idx[n] for n in mnames])
        d = np.asarray(sd, dtype=np.float64)
        ok = np.isfinite(d)
        total[np.ix_(ix, ix)] += np.where(ok, d, 0.0)
        count[np.ix_(ix, ix)] += ok
    comb = np.full((k, k), np.nan)
    np.divide(total, count, out=comb, where=count > 0)
    return names, comb


def species_level_status(names: list[str], comb: np.ndarray) -> dict[str, str]:
    """Nearest-neighbour test per species (species level, works for marker combinations).

    A species is evaluated when its own smallest conspecific distance (diagonal) is known and at
    least one other species can be compared. success: conspecific < nearest other species;
    ambiguous: equal (tie, e.g. both 0); fail: nearest other species is closer.
    """
    out: dict[str, str] = {}
    for i, name in enumerate(names):
        intra = comb[i, i]
        others = np.delete(comb[i], i)
        others = others[np.isfinite(others)]
        if not np.isfinite(intra) or others.size == 0:
            continue
        inter = others.min()
        out[name] = "success" if intra < inter - EPS else ("ambiguous" if abs(intra - inter) <= EPS else "fail")
    return out
