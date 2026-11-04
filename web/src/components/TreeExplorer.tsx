"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import SpeciesSearch from "./SpeciesSearch";
import TreeViewer from "./TreeViewer";
import { loadSpeciesIndex, loadTree } from "@/lib/data.client";
import { DISCRIMINATION_NOTE } from "./treeNotes";
import type { FamilyEntry, SpeciesIndexEntry, TreeFile } from "@/lib/types";

interface Props {
  families: FamilyEntry[];
  markers: string[];
}

/** Family + marker selectors, species highlighter and the tree itself. State lives in the URL. */
export default function TreeExplorer({ families, markers }: Props) {
  const router = useRouter();
  const params = useSearchParams();

  const family = families.find((f) => f.family === params.get("aile")) ?? families[0];
  const available = [...new Set(family.trees.map((t) => t.marker))];
  const wantedMarker = params.get("marker");
  const marker = wantedMarker && available.includes(wantedMarker) ? wantedMarker : available[0] ?? null;
  const speciesSlug = params.get("tur");

  const wantedGroup = params.get("grup");
  const [loadedTree, setLoadedTree] = useState<TreeFile | null>(null);
  const [failedFile, setFailedFile] = useState<string | null>(null);
  const [index, setIndex] = useState<SpeciesIndexEntry[]>([]);

  useEffect(() => {
    loadSpeciesIndex().then(setIndex);
  }, []);

  // large families are analysed genus by genus: several trees per marker
  const groups = family.trees.filter((t) => t.marker === marker).sort((a, b) => b.leaves - a.leaves);
  const selectedForGenus = index.find((s) => s.slug === speciesSlug)?.genus;
  const group =
    groups.find((g) => g.group === wantedGroup) ??
    groups.find((g) => selectedForGenus && g.group === `${family.family}/${selectedForGenus}`) ??
    groups[0] ??
    null;
  const file = group?.file ?? null;
  useEffect(() => {
    if (file) loadTree(file).then(setLoadedTree).catch(() => setFailedFile(file));
  }, [file]);
  // ignore a tree that belongs to the previous selection
  const tree = loadedTree && loadedTree.file === file ? loadedTree : null;
  const error = failedFile !== null && failedFile === file;

  const selected = useMemo(() => index.find((s) => s.slug === speciesSlug) ?? null, [index, speciesSlug]);

  const setParams = (next: { aile?: string; marker?: string | null; tur?: string | null; grup?: string | null }) => {
    const q = new URLSearchParams();
    q.set("aile", next.aile ?? family.family);
    const m = next.marker === undefined ? marker : next.marker;
    if (m) q.set("marker", m);
    const g = next.grup === undefined ? (next.marker === undefined && next.aile === undefined ? wantedGroup : null) : next.grup;
    if (g) q.set("grup", g);
    const t = next.tur === undefined ? speciesSlug : next.tur;
    if (t) q.set("tur", t);
    router.replace(`/agaclar?${q.toString()}`, { scroll: false });
  };

  const select = "rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm";

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label className="text-sm">
          <span className="mb-1 block font-medium text-stone-600">Aile</span>
          <select
            className={select}
            value={family.family}
            onChange={(e) => setParams({ aile: e.target.value, marker: null, tur: null, grup: null })}
          >
            {families.map((f) => (
              <option key={f.family} value={f.family}>
                {f.family} ({f.species} tür)
              </option>
            ))}
          </select>
        </label>
        <div className="text-sm">
          <span className="mb-1 block font-medium text-stone-600">Marker</span>
          <div className="flex gap-1">
            {markers.map((m) => {
              const has = available.includes(m);
              return (
                <button
                  key={m}
                  type="button"
                  disabled={!has}
                  onClick={() => setParams({ marker: m })}
                  className={`rounded-lg border px-3 py-2 font-medium ${
                    m === marker
                      ? "border-emerald-600 bg-emerald-600 text-white"
                      : "border-stone-300 bg-white text-stone-700 hover:border-emerald-400"
                  } disabled:cursor-not-allowed disabled:opacity-40`}
                  title={has ? "" : "Bu aile için ağaç kurmaya yetecek dizi yok"}
                >
                  {m}
                </button>
              );
            })}
          </div>
        </div>
        {groups.length > 1 && (
          <label className="text-sm">
            <span className="mb-1 block font-medium text-stone-600">Cins grubu ({groups.length})</span>
            <select
              className={select}
              value={group?.group ?? ""}
              onChange={(e) => setParams({ grup: e.target.value, tur: null })}
            >
              {groups.map((g) => (
                <option key={g.group} value={g.group}>
                  {g.group.split("/")[1] ?? g.group} ({g.species} tür, {g.leaves} dizi)
                </option>
              ))}
            </select>
          </label>
        )}
        <div className="min-w-64 flex-1 text-sm">
          <span className="mb-1 block font-medium text-stone-600">Türü vurgula</span>
          <SpeciesSearch
            size="sm"
            family={family.family}
            placeholder={`${family.family} içinde tür ara…`}
            onSelect={(s) => setParams({ tur: s.slug })}
          />
        </div>
        {selected && (
          <div className="text-sm">
            <span className="mb-1 block font-medium text-stone-600">Seçili tür</span>
            <span className="inline-flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2">
              <Link href={`/turler/${selected.slug}`} className="font-medium italic text-red-700 hover:underline">
                {selected.name}
              </Link>
              <button type="button" className="text-stone-500 hover:text-stone-900" aria-label="Seçimi kaldır" onClick={() => setParams({ tur: null })}>
                ✕
              </button>
            </span>
          </div>
        )}
      </div>

      {!marker && (
        <p className="rounded-xl bg-amber-50 p-4 text-amber-900">
          {family.family} için hiçbir markerde ağaç kurmaya yetecek (en az 3) dizi yok.
        </p>
      )}
      {error && <p className="text-red-700">Ağaç yüklenemedi.</p>}
      {marker && !tree && !error && <p className="text-stone-500">Ağaç yükleniyor…</p>}
      {tree && (
        <>
          <p className="mb-2 text-sm text-stone-600">
            {tree.family} · {tree.marker}: {tree.n_leaves} dizi, {tree.n_species} tür · komşu birleştirme (NJ),
            p-mesafesi · hizalama: <strong>{tree.aligner}</strong>{tree.aligner !== "MAFFT" && " — ön sonuç"}
          </p>
          <TreeViewer
            tree={tree}
            highlight={selected?.name ?? null}
            height={640}
            onSelectSpecies={(name) => {
              const hit = index.find((s) => s.name === name);
              if (hit) setParams({ tur: hit.slug });
            }}
          />
          <p className="mt-3 text-sm text-stone-500">{DISCRIMINATION_NOTE}</p>
        </>
      )}
    </div>
  );
}
