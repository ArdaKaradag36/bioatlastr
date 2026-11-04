"""Tests for the sequence/name quality filters."""

import pytest

from barcode_atlas.filters import (
    check_name,
    check_sequence,
    clean_sequence,
    n_fraction,
    species_binomial,
)
from barcode_atlas.gbif import is_clean_binomial

TARGET = "Quercus robur"


@pytest.mark.parametrize(
    "organism, expected",
    [
        ("Quercus robur", "Quercus robur"),
        ("Quercus robur subsp. robur", "Quercus robur"),
        ("Quercus", None),
        ("uncultured bacterium", None),
        ("", None),
        (None, None),
    ],
)
def test_species_binomial(organism, expected):
    assert species_binomial(organism) == expected


def test_good_record_passes():
    assert check_name("Quercus robur", "Quercus robur rbcL gene, partial cds", TARGET) is None


def test_subspecies_is_accepted_as_species():
    assert check_name("Quercus robur subsp. broutii", "x", TARGET) is None


@pytest.mark.parametrize(
    "organism, reason",
    [
        ("Quercus sp.", "ambiguous_sp"),
        ("Quercus sp. TUR-12", "ambiguous_sp"),
        ("Quercus cf. robur", "ambiguous_cf"),
        ("Quercus aff. robur", "ambiguous_aff"),
        ("Quercus x rosacea", "hybrid"),
        ("Quercus × rosacea", "hybrid"),
        ("Quercus robur x Quercus petraea", "hybrid"),
        ("Quercus", "not_binomial"),
        ("", "no_organism"),
    ],
)
def test_ambiguous_names_are_dropped(organism, reason):
    assert check_name(organism, "some definition", TARGET) == reason


def test_unverified_definition_is_dropped():
    assert check_name("Quercus robur", "UNVERIFIED: Quercus robur rbcL", TARGET) == "unverified"


def test_name_mismatch_is_dropped_unless_allowed():
    assert check_name("Quercus petraea", "x", TARGET) == "name_mismatch"
    assert check_name("Quercus petraea", "x", TARGET, allow_name_mismatch=True) is None


def test_clean_sequence():
    assert clean_sequence("acgu nn\n12-.") == "ACGTNN"


def test_n_fraction():
    assert n_fraction("ACNN") == 0.5
    assert n_fraction("") == 0.0


def test_sequence_length_filter():
    seq = "A" * 399
    assert check_sequence(seq, min_length=400, max_n_fraction=0.02) == "too_short"
    assert check_sequence("A" * 400, min_length=400, max_n_fraction=0.02) is None


def test_sequence_n_filter():
    # 3 N in 100 bases = 3% > 2%
    seq = "A" * 97 + "NNN"
    assert check_sequence(seq, 50, 0.02) == "too_many_N"
    # exactly 2% is still allowed
    assert check_sequence("A" * 98 + "NN", 50, 0.02) is None


def test_sequence_invalid_and_empty():
    assert check_sequence("", 10, 0.1) == "empty_sequence"
    assert check_sequence("ACGT" * 20 + "!", 10, 0.1) == "invalid_characters"


def test_gbif_binomial_check():
    assert is_clean_binomial("Quercus robur")
    assert not is_clean_binomial("Quercus x rosacea")
    assert not is_clean_binomial("Quercus robur subsp. robur")
    assert not is_clean_binomial(None)
