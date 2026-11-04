import pandas as pd

from barcode_atlas.wcvp import build_species_table


def names():
    cols = ["plant_name_id", "taxon_rank", "taxon_status", "family", "genus_hybrid", "genus", "species_hybrid",
            "species", "taxon_authors", "accepted_plant_name_id", "powo_id"]
    rows = [
        ("1", "Species", "Accepted", "Fagaceae", "", "Quercus", "", "robur", "L.", "1", "p1"),
        ("2", "Species", "Accepted", "Fagaceae", "", "Quercus", "", "introduced", "", "2", ""),
        ("3", "Species", "Accepted", "Fagaceae", "", "Quercus", "", "extinct", "", "3", ""),
        ("4", "Species", "Accepted", "Fagaceae", "", "Quercus", "", "doubt", "", "4", ""),
        ("5", "Species", "Accepted", "Fagaceae", "", "Quercus", "×", "hyb", "", "5", ""),
        ("6", "Variety", "Accepted", "Fagaceae", "", "Quercus", "", "robur", "", "6", ""),
        ("7", "Species", "Accepted", "Lamiaceae", "", "Sideritis", "", "endem", "", "7", ""),
        ("8", "Species", "Synonym", "Fagaceae", "", "Quercus", "", "pedunculata", "", "1", ""),
        ("9", "Species", "Accepted", "Rosaceae", "", "Rosa", "", "abroad", "", "9", ""),
        ("10", "Species", "Synonym", "Lamiaceae", "", "Burgsdorfia", "", "endem", "", "7", ""),
    ]
    return pd.DataFrame(rows, columns=cols)


def dist():
    cols = ["plant_name_id", "area_code_l3", "area", "introduced", "extinct", "location_doubtful"]
    rows = [
        ("1", "TUR", "Türkiye", "0", "0", "0"), ("1", "FRA", "France", "0", "0", "0"),
        ("2", "TUR", "Türkiye", "1", "0", "0"), ("3", "TUR", "Türkiye", "0", "1", "0"),
        ("4", "TUR", "Türkiye", "0", "0", "1"), ("5", "TUR", "Türkiye", "0", "0", "0"),
        ("6", "TUR", "Türkiye", "0", "0", "0"), ("7", "TUR", "Türkiye", "0", "0", "0"),
        ("7", "EGY", "Egypt", "1", "0", "0"), ("9", "FRA", "France", "0", "0", "0"),
    ]
    return pd.DataFrame(rows, columns=cols)


def test_filters_and_endemic_flag():
    table, syn, stats = build_species_table(names(), dist(), "TUR")
    assert list(table["species"]) == ["Quercus robur", "Sideritis endem"]
    assert dict(zip(table["species"], table["endemic"])) == {"Quercus robur": 0, "Sideritis endem": 1}
    assert stats["hybrids_excluded"] == 1


def test_synonyms_only_of_kept_species():
    _, syn, _ = build_species_table(names(), dist(), "TUR")
    assert set(zip(syn["synonym"], syn["accepted"])) == {
        ("Quercus pedunculata", "Quercus robur"), ("Burgsdorfia endem", "Sideritis endem")}
