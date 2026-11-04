// Build-time data access for server components (reads the pipeline's JSON files).
import "server-only";
import fs from "node:fs";
import path from "node:path";
import type { FamilyEntry, GapsFile, Meta, SpeciesIndexEntry,
  TaxonNames, Stats } from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");
const memo = new Map<string, unknown>();

// Files are read once per build process (thousands of species pages reuse them).
function readJson<T>(file: string): T {
  if (memo.has(file)) return memo.get(file) as T;
  const full = path.join(DATA_DIR, file);
  if (!fs.existsSync(full)) {
    throw new Error(
      `Veri dosyası bulunamadı: ${full}\nÖnce Python hattını çalıştırın (README.md).`,
    );
  }
  const value = JSON.parse(fs.readFileSync(full, "utf-8")) as T;
  memo.set(file, value);
  return value;
}

export const getGaps = () => readJson<GapsFile>("gaps.json");
export const getTaxonNames = () => readJson<TaxonNames>("taxon_names.json");
export const getMeta = () => readJson<Meta>("meta.json");
export const getStats = () => readJson<Stats>("stats.json");
export const getFamilies = () => readJson<FamilyEntry[]>("families.json");
export const getSpeciesIndex = () => readJson<SpeciesIndexEntry[]>("species_index.json");

/** slug -> index entry, built once. */
export function getSpeciesBySlug(): Map<string, SpeciesIndexEntry> {
  const key = "by_slug";
  if (!memo.has(key)) memo.set(key, new Map(getSpeciesIndex().map((s) => [s.slug, s])));
  return memo.get(key) as Map<string, SpeciesIndexEntry>;
}
