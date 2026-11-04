"""Phase 5 - publication-style PNG figures in results/figures (needs phase 3 output).

Usage (from the repository root):  python pipeline/phase5_figures.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from barcode_atlas.figures import make_figures  # noqa: E402

if __name__ == "__main__":
    print("figures:", ", ".join(make_figures()))
