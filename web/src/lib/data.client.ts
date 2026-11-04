// Browser-side data access: fetch JSON files from /data and keep them in memory.
import type {
  FamilyEntry,
  GapsFile,
  ReferenceRecord,
  SpeciesDetail,
  SpeciesIndexEntry,
  TaxonNames,
  TreeFile,
} from "./types";

const cache = new Map<string, Promise<unknown>>();

export function fetchJson<T>(path: string): Promise<T> {
  let p = cache.get(path) as Promise<T> | undefined;
  if (!p) {
    p = fetch(`/data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
      return r.json() as Promise<T>;
    });
    // do not keep failed requests in the cache
    p.catch(() => cache.delete(path));
    cache.set(path, p);
  }
  return p;
}

export const loadSpeciesIndex = () => fetchJson<SpeciesIndexEntry[]>("species_index.json");
export const loadFamilies = () => fetchJson<FamilyEntry[]>("families.json");
/** Species details are stored one file per genus (slug "quercus-robur" -> species/quercus.json). */
export const loadSpecies = (slug: string) =>
  fetchJson<Record<string, SpeciesDetail>>(`species/${slug.split("-")[0]}.json`).then((m) => m[slug] ?? null);
export const loadTree = (file: string) => fetchJson<TreeFile>(`trees/${file}.json`);
export const loadReference = (marker: string) =>
  fetchJson<ReferenceRecord[]>(`reference/${marker}.json`);

export const loadGaps = () => fetchJson<GapsFile>("gaps.json");

export const loadTaxonNames = () => fetchJson<TaxonNames>("taxon_names.json");
