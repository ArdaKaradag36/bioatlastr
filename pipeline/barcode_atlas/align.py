"""Multiple sequence alignment.

1. If the `mafft` binary is available we use it (best quality).
2. Otherwise we print install instructions and fall back to a simple
   "center star" alignment built with Biopython's PairwiseAligner.
   It is less accurate than MAFFT but keeps the pipeline runnable.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

from Bio.Align import PairwiseAligner
from Bio.Seq import Seq

INSTALL_HELP = """
MAFFT was not found on PATH. The pipeline will use a simpler Biopython-based
fallback aligner (results are usable but MAFFT is more accurate).

To install MAFFT:
  Windows : download the installer from https://mafft.cbrc.jp/alignment/software/windows.html
            (or run inside WSL: sudo apt install mafft), then restart the terminal.
  macOS   : brew install mafft
  Linux   : sudo apt install mafft      (Debian/Ubuntu)
            sudo dnf install mafft      (Fedora)
            conda install -c bioconda mafft
  Then check with:  mafft --version
You can also point to a custom binary with `analysis.mafft_path` in the config
or the MAFFT_BINARY environment variable.
"""

_warned = False


def find_mafft(configured: str | None = None) -> str | None:
    """Path of the mafft binary or None."""
    for candidate in (configured, os.environ.get("MAFFT_BINARY")):
        if candidate and Path(candidate).exists():
            return str(candidate)
    found = shutil.which("mafft")
    if found:
        return found
    # user-level micromamba install (see README): ~/tools/mamba/envs/mafft/bin/mafft
    user = Path.home() / "tools" / "mamba" / "envs" / "mafft" / "bin" / "mafft"
    return str(user) if user.exists() else None


def print_install_help_once() -> None:
    global _warned
    if not _warned:
        print(INSTALL_HELP)
        _warned = True


class AlignTimeout(RuntimeError):
    """MAFFT exceeded the per-group time limit (the group is skipped and logged, never retried)."""


def align_mafft(seqs: dict[str, str], mafft: str, threads: int = -1, timeout: float | None = None) -> dict[str, str]:
    """Run MAFFT. Returns {id: aligned sequence} in the same order as the input."""
    ids = list(seqs)
    with tempfile.TemporaryDirectory() as tmp:
        infile = Path(tmp) / "in.fasta"
        # Short safe ids (s0, s1, ...) so odd characters never confuse MAFFT.
        with open(infile, "w") as fh:
            for i, key in enumerate(ids):
                fh.write(f">s{i}\n{seqs[key]}\n")
        # --auto picks an accurate (slow) strategy for medium groups; above 400 sequences use FFT-NS-2 (fast, still MAFFT)
        strategy = ["--retree", "2", "--maxiterate", "0"] if len(ids) > 400 else ["--auto"]
        cmd = [mafft, *strategy, "--quiet", "--adjustdirection", "--thread", str(threads), str(infile)]
        # own process group so the whole MAFFT pipeline (the wrapper script spawns children) dies on timeout
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            out, err = popen.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(popen.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            popen.communicate()
            raise AlignTimeout(f"MAFFT timeout after {timeout}s for {len(ids)} sequences")
        proc = subprocess.CompletedProcess(cmd, popen.returncode, out, err)
    if proc.returncode != 0:
        raise RuntimeError(f"mafft failed: {proc.stderr[:300]}")

    aligned: dict[str, str] = {}
    current: str | None = None
    parts: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith(">"):
            if current is not None:
                aligned[current] = "".join(parts).upper()
            name = line[1:].strip()
            if name.startswith("_R_"):  # --adjustdirection marks reversed sequences
                name = name[3:]
            current, parts = name, []
        else:
            parts.append(line.strip())
    if current is not None:
        aligned[current] = "".join(parts).upper()
    return {key: aligned[f"s{i}"] for i, key in enumerate(ids)}


# ---------------------------------------------------------------------------
# Fallback: center-star alignment with Biopython
# ---------------------------------------------------------------------------
def _make_aligner() -> PairwiseAligner:
    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 2.0
    aligner.mismatch_score = -1.0
    aligner.open_gap_score = -3.0
    aligner.extend_gap_score = -0.5
    aligner.end_gap_score = 0.0  # free end gaps: sequences have different lengths
    return aligner


def _reverse_complement(seq: str) -> str:
    return str(Seq(seq).reverse_complement())


def _pairwise_to_center(aligner: PairwiseAligner, center: str, seq: str):
    """Align seq to center (try both strands). Return (columns, insertions, score, seq_used)."""
    best = None
    for candidate in (seq, _reverse_complement(seq)):
        aln = aligner.align(center, candidate)[0]
        if best is None or aln.score > best[0].score:
            best = (aln, candidate)
    aln, used = best

    m = len(center)
    match_col = [-1] * m  # center position -> index in seq (or -1 = gap)
    inserts: dict[int, str] = {}  # center position -> residues of seq inserted before it
    prev_t, prev_q = 0, 0
    for (t0, t1), (q0, q1) in zip(*[_pairs(aln.aligned[0]), _pairs(aln.aligned[1])]):
        if q0 > prev_q:  # residues of seq with no partner in the center
            inserts[prev_t] = inserts.get(prev_t, "") + used[prev_q:q0]
        for k in range(t1 - t0):
            match_col[t0 + k] = q0 + k
        prev_t, prev_q = t1, q1
    if prev_q < len(used):
        inserts[prev_t] = inserts.get(prev_t, "") + used[prev_q:]
    return match_col, inserts, aln.score, used


def _pairs(blocks):
    return [(int(a), int(b)) for a, b in blocks]


def align_fallback(seqs: dict[str, str], sample_size: int = 12) -> dict[str, str]:
    """Center-star multiple alignment (simple, approximate).

    1. choose a "center" sequence (best average score against a small sample)
    2. align every sequence to the center (free end gaps, both strands)
    3. merge all pairwise alignments by adding gap columns where sequences insert residues
    """
    ids = list(seqs)
    if len(ids) == 1:
        return dict(seqs)
    aligner = _make_aligner()

    # --- choose the center ---
    sample = sorted(ids, key=lambda k: -len(seqs[k]))[: sample_size]
    best_id, best_total = sample[0], -1e18
    for cand in sample:
        total = sum(aligner.score(seqs[cand], seqs[o]) for o in sample if o != cand)
        if total > best_total:
            best_id, best_total = cand, total
    center = seqs[best_id]
    m = len(center)

    # --- pairwise alignments to the center ---
    per_seq = {}
    max_insert = [0] * (m + 1)
    for key in ids:
        if key == best_id:
            continue
        match_col, inserts, _, used = _pairwise_to_center(aligner, center, seqs[key])
        per_seq[key] = (match_col, inserts, used)
        for pos, text in inserts.items():
            max_insert[pos] = max(max_insert[pos], len(text))

    # --- merge into one alignment ---
    def build(key: str) -> str:
        if key == best_id:
            match_col, inserts, used = list(range(m)), {}, center
        else:
            match_col, inserts, used = per_seq[key]
        out: list[str] = []
        for pos in range(m + 1):
            ins = inserts.get(pos, "")
            out.append(ins + "-" * (max_insert[pos] - len(ins)))
            if pos < m:
                out.append(used[match_col[pos]] if match_col[pos] >= 0 else "-")
        return "".join(out)

    return {key: build(key) for key in ids}


def align_sequences(
    seqs: dict[str, str], mafft_path: str | None = None, threads: int = -1, timeout: float | None = None
) -> tuple[dict[str, str], str]:
    """Align sequences. Returns (aligned, method) where method is 'mafft' or 'center-star'."""
    if len(seqs) < 2:
        return dict(seqs), "none"
    mafft = find_mafft(mafft_path)
    if mafft:
        try:
            return align_mafft(seqs, mafft, threads, timeout), "mafft"
        except AlignTimeout:
            raise
        except Exception as exc:  # fall through to the pure-Python aligner
            print(f"  ! MAFFT failed ({exc}); using fallback aligner")
    else:
        print_install_help_once()
    return align_fallback(seqs), "center-star"
