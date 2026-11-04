"""Phase 2 - download and filter barcode sequences (default: ENA).

Usage (from the repository root):
    python pipeline/phase2_sequences.py --config pipeline/config.test.yaml
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.config import load_config  # noqa: E402
from barcode_atlas.sources import run_phase2  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    args = parser.parse_args()
    cfg = load_config(args.config)
    run_phase2(cfg)


if __name__ == "__main__":
    main()
