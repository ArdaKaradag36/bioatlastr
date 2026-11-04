"""Phase 3 safeguards: subsampling, MAFFT timeout, failing groups never stop the run."""
import stat
import pandas as pd
import pytest

from barcode_atlas import analysis
from barcode_atlas.align import AlignTimeout, align_mafft


def test_subsample_keeps_turkish_and_one_per_species():
    rows = []
    for sp in "ABCDE":
        for i in range(4):
            rows.append({"species": sp, "accession": f"{sp}{i}", "is_turkey": 1 if (sp in "AB" and i == 3) else 0})
    out = analysis.subsample_group(pd.DataFrame(rows), 7)
    assert len(out) == 7
    assert {"A3", "B3"} <= set(out["accession"])          # Turkish records first
    assert set(out["species"]) == set("ABCDE")            # every species represented
    assert len(analysis.subsample_group(pd.DataFrame(rows), 100)) == 20


def test_mafft_timeout_kills_process(tmp_path):
    fake = tmp_path / "mafft"
    fake.write_text("#!/bin/sh\nsleep 30\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(AlignTimeout):
        align_mafft({"a": "ACGT", "b": "ACGA"}, str(fake), 1, timeout=1)


def test_failing_group_is_reported_not_raised(monkeypatch):
    def boom(*a, **k):
        raise AlignTimeout("too slow")
    monkeypatch.setattr(analysis, "_compute_group", boom)
    res = analysis.compute_group({"key": "F", "marker": "rbcL", "sub": None})
    assert res["failed"] == "skipped: too large/timeout"
    monkeypatch.setattr(analysis, "_compute_group", lambda j: 1 / 0)
    assert analysis.compute_group({"key": "F"})["failed"] == "skipped: error"
