import sys
from pathlib import Path

# Make "barcode_atlas" importable when pytest runs from any folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
