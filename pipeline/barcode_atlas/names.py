"""Name matching: ENA/GenBank organism names -> accepted WCVP species of Turkey.

Pure functions (no network, no files) so they are easy to test.
"""

from __future__ import annotations

from typing import Iterable

from .filters import check_name, species_binomial


def build_name_index(
    accepted: Iterable[str],
    synonyms: Iterable[tuple[str, str]] = (),
) -> dict[str, tuple[str | None, str]]:
    """binomial -> (accepted species | None, 'accepted' | 'synonym' | 'ambiguous').

    accepted  - accepted Turkish species names (species.csv)
    synonyms  - (synonym binomial, accepted binomial) pairs from WCVP; only pairs whose
                accepted name is in `accepted` are used. A synonym that points to two
                different accepted species is ambiguous and never matched.
    """
    acc = set(accepted)
    index: dict[str, tuple[str | None, str]] = {a: (a, "accepted") for a in acc}
    targets: dict[str, set[str]] = {}
    for syn, target in synonyms:
        if target in acc and syn not in acc:
            targets.setdefault(syn, set()).add(target)
    for syn, tset in targets.items():
        index[syn] = (next(iter(tset)), "synonym") if len(tset) == 1 else (None, "ambiguous")
    return index


def epithet_variants(epithet: str) -> list[str]:
    """Latin gender variants of a species epithet (arvensis/arvense, alba/albus/album)."""
    for ending, others in (("us", ("a", "um")), ("a", ("us", "um")), ("um", ("us", "a")),
                           ("is", ("e",)), ("e", ("is",))):
        if epithet.endswith(ending) and len(epithet) > len(ending) + 2:
            stem = epithet[: -len(ending)]
            return [stem + o for o in others]
    return []


def _lookup(index: dict[str, tuple[str | None, str]], candidates: list[str]) -> tuple[str | None, str]:
    """(accepted, via) when all hits agree on one accepted species; (None, 'ambiguous') for conflicts."""
    hits = {index[c][0] for c in candidates if c in index and index[c][0] is not None}
    if len(hits) == 1:
        return next(iter(hits)), "ok"
    return (None, "ambiguous") if hits else (None, "none")


def match_record(
    organism: str | None,
    description: str | None,
    index: dict[str, tuple[str | None, str]],
    genus_alias: dict[str, list[str]] | None = None,
) -> tuple[str | None, str, str | None]:
    """Return (accepted species, 'accepted'|'synonym', None) or (None, '', reason).

    Reasons: no_organism, ambiguous_sp, ambiguous_cf, ambiguous_aff, hybrid, unverified,
    not_binomial, ambiguous_synonym, unmatched_name.
    """
    binomial = species_binomial(organism)
    # check_name with the record's own binomial as target tests everything except the match itself
    reason = check_name(organism, description, binomial or "", allow_name_mismatch=True)
    if reason:
        return None, "", reason
    assert binomial is not None  # check_name returns not_binomial otherwise
    hit = index.get(binomial)
    if hit is None:
        # fallbacks: Latin gender variants of the epithet, and WCVP genera that ENA/NCBI files under the
        # record's genus (e.g. WCVP "Acinos" -> ENA "Clinopodium": record "Clinopodium arvense" = "Acinos arvensis")
        genus, epithet = binomial.split(" ", 1)
        epithets = [epithet] + epithet_variants(epithet)
        tries = [("epithet_variant", [f"{genus} {e}" for e in epithets[1:]])]
        tries.append(("genus_synonym", [f"{g} {e}" for g in (genus_alias or {}).get(genus, []) for e in epithets]))
        for via, cands in tries:
            acc, status = _lookup(index, cands)
            if status == "ambiguous":
                return None, "", "ambiguous_synonym"
            if acc:
                return acc, via, None
        return None, "", "unmatched_name"
    accepted, via = hit
    if accepted is None:
        return None, "", "ambiguous_synonym"
    return accepted, via, None
