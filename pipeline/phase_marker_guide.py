"""Build the paired marker recommendation guide from existing discrimination results.

Usage (from repository root):
    python pipeline/phase_marker_guide.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.config import load_config  # noqa: E402
from barcode_atlas.marker_guide import run_marker_guide  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    args = parser.parse_args()
    summary = run_marker_guide(load_config(args.config))
    print(
        f"recommended={summary['n_recommended']} yetersiz={summary['n_yetersiz']} "
        f"belirsiz={summary['n_belirsiz']}",
        flush=True,
    )
    for ex in summary["summary"].query("recommendation in ['rbcL','matK','ITS']").head(3).itertuples():
        print(f"  {ex.family}: {ex.recommendation} (n={ex.n_species_behind})", flush=True)


if __name__ == "__main__":
    main()
