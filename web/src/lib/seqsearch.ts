// Sequence search in the browser: k-mer shortlist + pairwise alignment identity.
//
// 1. k-mer filter: count how many k-mers of every reference also occur in the query
//    (both strands) -> keep the best candidates.
// 2. For every candidate run a semi-global alignment (free end gaps) and compute
//    identity = matches / aligned columns inside the overlapping region.
// The result is only indicative; it is NOT a replacement for BLAST / a tree analysis.

import type { ReferenceRecord } from "./types";

export const TOP_N_MATCHES = 5;
export const MIN_QUERY_LENGTH = 50;
export const MAX_QUERY_LENGTH = 3000;
const K = 8;
const CANDIDATES = 40;
export const MIN_OVERLAP = 100; // bases that must overlap for a hit to be ranked

const MATCH = 2;
const MISMATCH = -3;
const GAP = -4;

export interface SearchHit {
  accession: string;
  species: string;
  identity: number; // 0..1 over the aligned (overlapping) region
  alignedLength: number; // columns of the alignment
  queryCoverage: number; // fraction of the query that overlaps the reference
  reverseComplement: boolean;
  /** Ranking score: identity x overlap fraction of the shorter sequence (see searchReference). */
  rank: number;
}

/** Remove FASTA header lines, whitespace and digits; upper-case; U -> T. */
export function cleanQuery(text: string): string {
  return text
    .split(/\r?\n/)
    .filter((l) => !l.startsWith(">"))
    .join("")
    .replace(/[^A-Za-z]/g, "")
    .toUpperCase()
    .replace(/U/g, "T");
}

export function invalidCharacters(seq: string): string[] {
  return Array.from(new Set(seq.replace(/[ACGTRYSWKMBDHVN]/g, "").split("")));
}

const COMPLEMENT: Record<string, string> = {
  A: "T", C: "G", G: "C", T: "A", R: "Y", Y: "R", S: "S", W: "W",
  K: "M", M: "K", B: "V", D: "H", H: "D", V: "B", N: "N",
};

export function reverseComplement(seq: string): string {
  let out = "";
  for (let i = seq.length - 1; i >= 0; i--) out += COMPLEMENT[seq[i]] ?? "N";
  return out;
}

const BASE_CODE: Record<string, number> = { A: 0, C: 1, G: 2, T: 3 };

/** Bitmap with a 1 for every k-mer present in the sequence. */
function kmerSet(seq: string): Uint8Array {
  const set = new Uint8Array(1 << (2 * K));
  const mask = (1 << (2 * K)) - 1;
  let code = 0;
  let valid = 0;
  for (let i = 0; i < seq.length; i++) {
    const b = BASE_CODE[seq[i]];
    if (b === undefined) {
      valid = 0;
      code = 0;
      continue;
    }
    code = ((code << 2) | b) & mask;
    valid++;
    if (valid >= K) set[code] = 1;
  }
  return set;
}

/** Fraction of the reference's k-mers that are present in the query bitmap. */
function sharedFraction(ref: string, set: Uint8Array): number {
  const mask = (1 << (2 * K)) - 1;
  let code = 0;
  let valid = 0;
  let total = 0;
  let shared = 0;
  for (let i = 0; i < ref.length; i++) {
    const b = BASE_CODE[ref[i]];
    if (b === undefined) {
      valid = 0;
      code = 0;
      continue;
    }
    code = ((code << 2) | b) & mask;
    valid++;
    if (valid >= K) {
      total++;
      if (set[code]) shared++;
    }
  }
  return total ? shared / total : 0;
}

export interface AlignmentResult {
  identity: number;
  alignedLength: number;
  queryAligned: number;
}

/**
 * Semi-global alignment (free leading/trailing gaps in both sequences).
 * Identity is computed over the columns of the traced path only.
 */
export function overlapAlign(a: string, b: string): AlignmentResult {
  const m = a.length;
  const n = b.length;
  const w = n + 1;
  const score = new Int32Array((m + 1) * w); // first row/column stay 0 (free end gaps)
  const trace = new Uint8Array((m + 1) * w); // 1 diag, 2 up (gap in b), 3 left (gap in a)
  for (let i = 1; i <= m; i++) {
    const ai = a.charCodeAt(i - 1);
    for (let j = 1; j <= n; j++) {
      const s = ai === b.charCodeAt(j - 1) && ai !== 78 /* N */ ? MATCH : MISMATCH;
      const diag = score[(i - 1) * w + j - 1] + s;
      const up = score[(i - 1) * w + j] + GAP;
      const left = score[i * w + j - 1] + GAP;
      let best = diag;
      let t = 1;
      if (up > best) {
        best = up;
        t = 2;
      }
      if (left > best) {
        best = left;
        t = 3;
      }
      score[i * w + j] = best;
      trace[i * w + j] = t;
    }
  }
  // best end cell: last row or last column (free trailing gaps)
  let bi = m;
  let bj = 0;
  let best = -Infinity;
  for (let j = 0; j <= n; j++) {
    if (score[m * w + j] > best) {
      best = score[m * w + j];
      bi = m;
      bj = j;
    }
  }
  for (let i = 0; i <= m; i++) {
    if (score[i * w + n] > best) {
      best = score[i * w + n];
      bi = i;
      bj = n;
    }
  }
  let i = bi;
  let j = bj;
  let matches = 0;
  let columns = 0;
  let queryAligned = 0;
  while (i > 0 && j > 0) {
    const t = trace[i * w + j];
    if (t === 1) {
      if (a.charCodeAt(i - 1) === b.charCodeAt(j - 1) && a[i - 1] !== "N") matches++;
      queryAligned++;
      i--;
      j--;
    } else if (t === 2) {
      queryAligned++;
      i--;
    } else {
      j--;
    }
    columns++;
  }
  return { identity: columns ? matches / columns : 0, alignedLength: columns, queryAligned };
}

/** Search `query` against the reference records and return the best hits. */
export async function searchReference(
  query: string,
  refs: ReferenceRecord[],
  topN = TOP_N_MATCHES,
  onProgress?: (done: number, total: number) => void,
): Promise<SearchHit[]> {
  const rc = reverseComplement(query);
  const setFwd = kmerSet(query);
  const setRev = kmerSet(rc);

  // 1) shortlist by shared k-mers
  const scored = refs.map((r, idx) => {
    const f = sharedFraction(r[2], setFwd);
    const rv = sharedFraction(r[2], setRev);
    return { idx, score: Math.max(f, rv), reverse: rv > f };
  });
  scored.sort((x, y) => y.score - x.score);
  const shortlist = scored.slice(0, CANDIDATES);

  // 2) align the shortlist
  const hits: SearchHit[] = [];
  for (let k = 0; k < shortlist.length; k++) {
    const c = shortlist[k];
    const ref = refs[c.idx];
    const q = c.reverse ? rc : query;
    const aln = overlapAlign(q, ref[2]);
    hits.push({
      accession: ref[0],
      species: ref[1],
      identity: aln.identity,
      alignedLength: aln.alignedLength,
      queryCoverage: aln.queryAligned / query.length,
      reverseComplement: c.reverse,
      // A perfect match over a small part of the sequences must not beat a near-perfect
      // match over the whole barcode: weight identity by how much of the shorter sequence overlaps.
      rank: aln.identity * Math.min(1, aln.alignedLength / Math.min(query.length, ref[2].length)),
    });
    if (k % 5 === 4) {
      onProgress?.(k + 1, shortlist.length);
      await new Promise((resolve) => setTimeout(resolve, 0)); // keep the page responsive
    }
  }
  // A 100% match over a handful of bases means nothing: require a reasonable overlap.
  const minOverlap = Math.min(MIN_OVERLAP, Math.floor(query.length / 2));
  const usable = hits.filter((h) => h.alignedLength >= minOverlap);
  const ranked = usable.length > 0 ? usable : hits;
  // Best first: weighted score, then raw identity
  ranked.sort((x, y) => y.rank - x.rank || y.identity - x.identity);
  return ranked.slice(0, topN);
}
