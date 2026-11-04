"""Run phases 1, 2 and 3 one after the other.

Usage (from the repository root):
    python pipeline/run_all.py --config pipeline/config.test.yaml   # small test run
    python pipeline/run_all.py                                      # full dataset
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.analysis import analyse  # noqa: E402
from barcode_atlas.config import load_config  # noqa: E402
from barcode_atlas.export import export_all  # noqa: E402
from barcode_atlas.sources import run_phase1, run_phase2  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    parser.add_argument("--skip-phase1", action="store_true", help="reuse existing data/species.csv")
    parser.add_argument("--skip-phase2", action="store_true", help="reuse existing data/sequence_table.csv")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if not args.skip_phase1:
        run_phase1(cfg)
    if not args.skip_phase2:
        run_phase2(cfg)
    export_all(cfg, analyse(cfg))


if __name__ == "__main__":
    main()
