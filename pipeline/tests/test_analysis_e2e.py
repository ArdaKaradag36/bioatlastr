"""End-to-end test of phase 3 on a tiny synthetic dataset (fallback aligner, temp folders)."""

import random

import pandas as pd
import pytest

from barcode_atlas import analysis
from barcode_atlas.config import load_config
from pathlib import Path

CFG_PATH = Path(__file__).parents[1] / "config.yaml"


def mutate(seq, rate, rng):
    return "".join(rng.choice("ACGT") if rng.random() < rate else c for c in seq)


@pytest.fixture()
def dataset(tmp_path, monkeypatch):
    rng = random.Random(1)
    base = "".join(rng.choice("ACGT") for _ in range(600))
    species = []  # (species, genus, family)
    # Fam1: genus A has 3 distinct species, genus B 1 species; Fam2: only 1 species (skipped group)
    for sp, g, f in [("Aaa one", "Aaa", "Fam1"), ("Aaa two", "Aaa", "Fam1"), ("Aaa three", "Aaa", "Fam1"),
                     ("Bbb one", "Bbb", "Fam1"), ("Ccc one", "Ccc", "Fam2"), ("Ddd none", "Ddd", "Fam2")]:
        species.append((sp, g, f))
    sp_df = pd.DataFrame(species, columns=["species", "genus", "family"])
    sp_df["endemic"] = [1, 0, 0, 0, 1, 1]
    sp_df["authorship"] = ""
    sp_df["common_name_tr"] = ""
    sp_df["common_name_en"] = ""
    sp_df.to_csv(tmp_path / "species.csv", index=False)

    ancestors = {s: mutate(base, 0.15, rng) for s, _, _ in species}
    ancestors["Aaa two"] = ancestors["Aaa one"]  # identical to Aaa one -> indistinguishable pair
    rows, fasta = [], []
    for s, g, f in species[:5]:
        for k in range(3):
            acc = f"X{len(rows):05d}"
            seq = mutate(ancestors[s], 0.0 if s in ('Aaa one', 'Aaa two') else 0.002, rng)
            rows.append({"species": s, "family": f, "genus": g, "marker": "rbcL", "accession": acc, "length": len(seq),
                         "source_title": "", "definition": "d", "organism": s, "n_fraction": 0, "country": "Turkey" if k == 0 else "",
                         "voucher": "", "is_turkey": int(k == 0), "matched_via": "accepted", "source": "ENA"})
            fasta.append((acc, seq))
    pd.DataFrame(rows).to_csv(tmp_path / "table.csv", index=False)
    (tmp_path / "seq").mkdir()
    with open(tmp_path / "seq" / "rbcL.fasta", "w") as fh:
        for acc, seq in fasta:
            fh.write(f">{acc}\n{seq}\n")
    monkeypatch.setattr(analysis, "SPECIES_CSV", tmp_path / "species.csv")
    monkeypatch.setattr(analysis, "SEQUENCE_TABLE_CSV", tmp_path / "table.csv")
    monkeypatch.setattr(analysis, "SEQUENCES_DIR", tmp_path / "seq")
    monkeypatch.setattr(analysis, "ALIGNMENTS_DIR", tmp_path / "aln")
    monkeypatch.setattr(analysis, "find_mafft", lambda *_: None)
    cfg = load_config(CFG_PATH)
    cfg["markers"] = {"rbcL": cfg["markers"]["rbcL"]}
    cfg["analysis"]["workers"] = 1
    cfg["analysis"]["min_overlap"] = 100
    return cfg


def run(cfg):
    import barcode_atlas.align as align
    align.align_sequences.__globals__["find_mafft"] = lambda *_: None
    return analysis.analyse(cfg)


def test_family_level_groups_and_gaps(dataset):
    res = run(dataset)
    gm = res["groups"]
    assert set(gm["group"]) == {"Fam1"}                         # Fam2 has a single species -> skipped
    assert res["skipped"]["reason"].tolist() == ["single_species"]
    assert res["aligner_label"] == "fallback (preliminary)"
    # Aaa one / Aaa two share the same ancestor -> distance 0 pair
    pairs = res["pairs"]
    assert {frozenset((a, b)) for a, b in zip(pairs["species_a"], pairs["species_b"])} >= {frozenset(("Aaa one", "Aaa two"))}
    gaps = res["gaps"]
    assert list(gaps["species"]["species"]) == ["Ddd none"]
    assert list(gaps["endemics"]["species"]) == ["Ddd none"]
    assert list(gaps["genera"]["genus"]) == ["Ddd"]
    comb = res["combinations"]
    row = comb[(comb["scope"] == "ALL") & (comb["combination"] == "rbcL")].iloc[0]
    assert row["species_evaluated"] >= 3 and row["ambiguous"] >= 2     # the identical pair is a tie
    assert row["success"] + row["ambiguous"] + row["fail"] == row["species_evaluated"]


def test_large_family_is_split_by_genus(dataset):
    dataset["analysis"]["max_group_sequences"] = 5
    res = run(dataset)
    assert set(res["groups"]["group"]) == {"Fam1/Aaa"}   # genus Bbb has one species -> skipped
    skipped = res["skipped"]
    assert "Fam1/Bbb" in set(skipped["group"])
    assert res["family_marker"][("Fam1", "rbcL")]["split_by_genus"] is True
    assert res["family_marker"][("Fam1", "rbcL")]["trees"][0]["file"] == "Fam1.Aaa.rbcL"
