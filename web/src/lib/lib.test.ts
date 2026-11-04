// Run with: npm test   (Node's built-in test runner through tsx)
import assert from "node:assert/strict";
import test from "node:test";
import { layoutTree, parseLeafLabel, parseNewick } from "./newick";
import {
  cleanQuery,
  overlapAlign,
  reverseComplement,
  searchReference,
} from "./seqsearch";
import { citationText, CONTACT_EMAIL, PAGES_URL, PROJECT_FUNDING, PROJECT_VERSION, publicUrl, REPO_URL } from "./site";
import { normalize } from "./text";

test("parseNewick reads leaves, lengths and nesting", () => {
  const t = parseNewick("((A__1:0.1,B__2:0.2):0.05,C__3:0.3);");
  assert.equal(t.children.length, 2);
  assert.equal(t.children[0].children[1].name, "B__2");
  assert.equal(t.children[0].length, 0.05);
  assert.equal(t.children[1].length, 0.3);
});

test("parseNewick handles scientific notation and very deep trees", () => {
  const t = parseNewick("(A:1e-05,B:0.000000);");
  assert.equal(t.children[0].length, 1e-5);
  let s = "L0:1";
  for (let i = 1; i < 5000; i++) s = `(${s}:1,L${i}:1)`;
  const deep = parseNewick(s + ";");
  const lay = layoutTree(deep, "cladogram", 100);
  assert.equal(lay.leaves.length, 5000);
});

test("layoutTree places leaves in rows and uses branch lengths", () => {
  const t = parseNewick("((A:1,B:1):1,C:3);");
  const lay = layoutTree(t, "phylogram", 300, 10);
  assert.equal(lay.leaves.length, 3);
  assert.deepEqual(lay.leaves.map((i) => lay.nodes[i].y), [0, 10, 20]);
  assert.equal(Math.max(...lay.nodes.map((n) => n.x)), 300);
  assert.ok(lay.hasBranchLengths);
});

test("parseLeafLabel", () => {
  assert.deepEqual(parseLeafLabel("Quercus_robur__KX1.1"), {
    species: "Quercus robur",
    accession: "KX1.1",
  });
});

test("cleanQuery strips FASTA headers and junk", () => {
  assert.equal(cleanQuery(">seq1 test\nacg tu\n12ACG\n"), "ACGTTACG");
});

test("reverseComplement", () => {
  assert.equal(reverseComplement("AACGT"), "ACGTT");
});

test("overlapAlign gives 100% for identical sequences and handles end gaps", () => {
  const s = "ATGCGTACGTTAGCTAGCTAGGATCCGATCGATCGTAGCTAGCTAGGCTAAGCTT";
  assert.equal(overlapAlign(s, s).identity, 1);
  const sub = s.slice(10, 40);
  const r = overlapAlign(sub, s);
  assert.equal(r.identity, 1);
  assert.equal(r.alignedLength, sub.length);
  const mutated = s.slice(0, 20) + "T" + s.slice(21); // one substitution (original is A?)
  const mm = overlapAlign(mutated, s);
  assert.ok(mm.identity < 1 && mm.identity > 0.95);
});

test("searchReference finds the right species on both strands", async () => {
  const rnd = (n: number, seed: number) => {
    let x = seed;
    let out = "";
    for (let i = 0; i < n; i++) {
      x = (x * 1103515245 + 12345) & 0x7fffffff;
      out += "ACGT"[x % 4];
    }
    return out;
  };
  const a = rnd(600, 1);
  const b = rnd(600, 2);
  const c = a.slice(0, 300) + rnd(5, 9) + a.slice(305); // close to a
  const refs: [string, string, string][] = [
    ["A1", "Species a", a],
    ["B1", "Species b", b],
    ["C1", "Species c", c],
  ];
  const fwd = await searchReference(a.slice(50, 500), refs, 3);
  assert.equal(fwd[0].species, "Species a");
  assert.equal(fwd[0].identity, 1);
  const rev = await searchReference(reverseComplement(b.slice(100, 560)), refs, 3);
  assert.equal(rev[0].species, "Species b");
  assert.ok(rev[0].reverseComplement);
});

test("normalize folds Turkish letters", () => {
  assert.equal(normalize("Şeftali İğde ÇAM Öküz Ürün Iğdır"), "seftali igde cam okuz urun igdir");
});

test("a full-length near match beats a perfect match over a short overlap", async () => {
  const rnd = (n: number, seed: number) => {
    let x = seed;
    let out = "";
    for (let i = 0; i < n; i++) {
      x = (x * 1103515245 + 12345) & 0x7fffffff;
      out += "ACGT"[x % 4];
    }
    return out;
  };
  const full = rnd(500, 7);
  const mutated = full.slice(0, 250) + (full[250] === "A" ? "C" : "A") + full.slice(251);
  const tail = rnd(300, 8) + full.slice(0, 120); // overlaps the query only over 120 bp
  const refs: [string, string, string][] = [
    ["TAIL", "Species tail", tail],
    ["FULL", "Species full", mutated],
  ];
  const hits = await searchReference(full, refs, 2);
  assert.equal(hits[0].species, "Species full");
});

test("citation text matches site identity fields", () => {
  const text = citationText();
  assert.match(text, /Karadağ/);
  assert.match(text, /Menekşe/);
  assert.ok(text.includes(PROJECT_VERSION));
  assert.ok(text.includes(REPO_URL));
  assert.equal(CONTACT_EMAIL, "karadagardaa@gmail.com");
  assert.equal(PROJECT_FUNDING, "");
  assert.equal(PAGES_URL, "https://ardakaradag36.github.io/bioatlastr");
  assert.equal(publicUrl("/data/meta.json"), "/data/meta.json");
});

test("static path list stays small and includes English summary", async () => {
  const { STATIC_PATHS } = await import("./site");
  assert.ok(STATIC_PATHS.includes("/en"));
  assert.ok(STATIC_PATHS.length < 50);
});
