"""Quality filters for GenBank records.

These are small pure functions (no network, no files) so they are easy to test.
Every function returns None when the record is fine, or a short reason code
that is written to data/dropped_sequences.csv.
"""

from __future__ import annotations

import re

# Words in an organism name that mean "species not fully determined".
AMBIGUOUS_TOKENS = {
    "sp": "ambiguous_sp",
    "spp": "ambiguous_sp",
    "cf": "ambiguous_cf",
    "aff": "ambiguous_aff",
    "nr": "ambiguous_aff",
    "indet": "ambiguous_sp",
}
# Markers for infraspecific ranks; they are allowed and removed from the name.
INFRASPECIFIC_TOKENS = {"subsp", "ssp", "var", "f", "forma", "subvar", "varietas"}

BINOMIAL_RE = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+$")
ALLOWED_BASES = set("ACGTRYSWKMBDHVN")


def _token_key(token: str) -> str:
    """'cf.' -> 'cf', 'Sp.' -> 'sp'."""
    return token.strip().strip(".").lower()


def species_binomial(organism: str | None) -> str | None:
    """'Quercus robur subsp. robur' -> 'Quercus robur'. None if not a clean binomial."""
    if not organism:
        return None
    tokens = organism.split()
    if len(tokens) < 2:
        return None
    name = f"{tokens[0]} {tokens[1]}"
    return name if BINOMIAL_RE.match(name) else None


def check_name(
    organism: str | None,
    definition: str | None,
    target_species: str,
    allow_name_mismatch: bool = False,
) -> str | None:
    """Reject records whose species name is ambiguous, unverified, hybrid or different.

    organism        - organism name written in the GenBank record
    definition      - GenBank DEFINITION / title line
    target_species  - the GBIF accepted name we searched for
    """
    organism = (organism or "").strip()
    definition = (definition or "").strip()
    if not organism:
        return "no_organism"

    tokens = organism.split()
    keys = [_token_key(t) for t in tokens]

    # 1) ambiguous identification: sp., cf., aff., ...
    for key in keys[1:]:
        if key in AMBIGUOUS_TOKENS:
            return AMBIGUOUS_TOKENS[key]

    # 2) hybrids: "Quercus x rosacea", "Quercus × rosacea", "xCupressocyparis"
    if any(t in ("x", "×") or t.startswith("×") for t in (k.lower() for k in tokens[1:])):
        return "hybrid"
    if tokens[0].startswith(("×", "x")) and len(tokens[0]) > 1 and tokens[0][1].isupper():
        return "hybrid"
    if "hybrid" in organism.lower():
        return "hybrid"

    # 3) GenBank marks doubtful records with an "UNVERIFIED:" prefix in the definition.
    if definition.upper().startswith("UNVERIFIED") or "UNVERIFIED:" in definition.upper():
        return "unverified"

    # 4) must be a clean "Genus species" (infraspecific ranks are cut off)
    binomial = species_binomial(organism)
    if binomial is None:
        return "not_binomial"

    # 5) the name in the record must be the species we searched for
    if binomial != target_species and not allow_name_mismatch:
        return "name_mismatch"
    return None


def clean_sequence(raw: str) -> str:
    """Upper-case, remove gaps/whitespace/digits, RNA U -> T."""
    seq = re.sub(r"[\s\d\-\.\*]", "", raw).upper()
    return seq.replace("U", "T")


def n_fraction(seq: str) -> float:
    """Fraction of 'N' characters (0 for empty strings)."""
    return seq.count("N") / len(seq) if seq else 0.0


def check_sequence(seq: str, min_length: int, max_n_fraction: float) -> str | None:
    """Reject sequences that are empty, invalid, too short or contain too many Ns."""
    if not seq:
        return "empty_sequence"
    if not set(seq) <= ALLOWED_BASES:
        return "invalid_characters"
    if len(seq) < min_length:
        return "too_short"
    if n_fraction(seq) > max_n_fraction:
        return "too_many_N"
    return None
