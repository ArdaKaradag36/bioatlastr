"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import SpeciesSearch from "./SpeciesSearch";
import Term from "./Term";
import TreeHelp from "./TreeHelp";
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
  const [mobileTree, setMobileTree] = useState(false);

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

  const select = "min-h-11 rounded-lg border border-stone-300 bg-white px-3 py-2 text-base";
  const familySpecies = index.filter((s) => s.family === family.family);
  const byGenus = new Map<string, SpeciesIndexEntry[]>();
  for (const s of familySpecies) {
    const list = byGenus.get(s.genus) ?? [];
    list.push(s);
    byGenus.set(s.genus, list);
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label>
          <span className="mb-1 block font-medium text-stone-800">Aile seçin</span>
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
        <div>
          <span className="mb-1 block font-medium text-stone-800"><Term id="barkod-bolgesi">Barkod bölgesi</Term></span>
          <div className="flex gap-1">
            {markers.map((m) => {
              const has = available.includes(m);
              return (
                <button
                  key={m}
                  type="button"
                  disabled={!has}
                  onClick={() => setParams({ marker: m })}
                  className={`min-h-11 min-w-14 rounded-lg border px-3 py-2 font-medium ${
                    m === marker
                      ? "border-primary bg-primary text-on-dark"
                      : "border-stone-300 bg-white text-stone-700 hover:border-emerald-400"
                  } disabled:cursor-not-allowed disabled:opacity-40`}
                  title={has ? "" : "Bu aile için ağaç kurmaya yetecek dizi yok"}
                  aria-pressed={m === marker}
                >
                  {m}
                </button>
              );
            })}
          </div>
        </div>
        {groups.length > 1 && (
          <label>
            <span className="mb-1 block font-medium text-stone-800">Cins grubu ({groups.length}) <span className="font-normal text-stone-600">— büyük aileler cins cins çizildi</span></span>
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
        <div className="min-w-64 flex-1">
          <span className="mb-1 block font-medium text-stone-800">Seçili türü vurgula <span className="font-normal text-stone-600">— adını yazın ya da ağaçta bir yaprağa tıklayın</span></span>
          <SpeciesSearch
            size="sm"
            family={family.family}
            placeholder={`${family.family} içinde tür ara…`}
            onSelect={(s) => setParams({ tur: s.slug })}
          />
        </div>
        {selected && (
          <div>
            <span className="mb-1 block font-medium text-stone-800">Vurgulanan tür</span>
            <span className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-red-100 px-3 py-2">
              <Link href={`/turler/${selected.slug}`} className="font-medium italic text-red-700 hover:underline">
                {selected.name}
              </Link>
              <button type="button" className="min-h-9 rounded-md px-2 text-stone-800 hover:bg-white/60" aria-label="Vurguyu kaldır" onClick={() => setParams({ tur: null })}>
                Vurguyu kaldır ✕
              </button>
            </span>
          </div>
        )}
      </div>

      {!marker && (
        <p className="rounded-xl bg-amber-50 p-4 text-amber-900">
          {family.family} ailesi için hiçbir barkod bölgesinde ağaç kurmaya yetecek kadar dizi yok. Bu bir <Term id="veri-boslugu">veri boşluğudur</Term>.
        </p>
      )}
      {error && <p className="text-red-700">Ağaç yüklenemedi. Sayfayı yenileyip tekrar deneyin.</p>}
      {marker && !tree && !error && <p className="text-stone-600" role="status">Ağaç yükleniyor…</p>}
      <div className="mb-4 md:hidden">
        <p className="mb-2 text-stone-800">Cinslere göre tür listesi. İnce ağaç çizgisi ilk karede açılmaz.</p>
        <ul className="max-h-[28rem] space-y-3 overflow-y-auto rounded-2xl border border-stone-200 bg-white p-3">
          {[...byGenus.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([genus, species]) => (
            <li key={genus}>
              <p className="font-semibold italic">{genus}</p>
              <ul className="mt-1 space-y-1">
                {species.map((s) => (
                  <li key={s.slug}>
                    <Link className="flex min-h-11 items-center italic text-link underline" href={`/turler/${s.slug}`}>
                      {s.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
        {tree && (
          <button
            type="button"
            className="mt-3 flex min-h-12 w-full items-center justify-center rounded-xl bg-forest px-4 font-semibold text-on-dark"
            onClick={() => setMobileTree((v) => !v)}
          >
            {mobileTree ? "Ağacı gizle" : "Ağacı aç"}
          </button>
        )}
      </div>

      {tree && (
        <div className={mobileTree ? "block" : "hidden md:block"}>
          <p className="mb-3 text-stone-800">
            <strong>{tree.family}</strong> · {tree.marker}: {tree.n_leaves} dizi, {tree.n_species} tür. Ağaç, <Term id="p-mesafesi">p-mesafesi</Term> ve <Term id="nj">komşu birleştirme (NJ)</Term> yöntemiyle
            kuruldu; <Term id="hizalama">hizalama</Term>: <strong>{tree.aligner}</strong>{tree.aligner !== "MAFFT" && " — ön sonuç"}.
          </p>
          <TreeHelp />
          <TreeViewer
            tree={tree}
            highlight={selected?.name ?? null}
            height={640}
            onSelectSpecies={(name) => {
              const hit = index.find((s) => s.name === name);
              if (hit) setParams({ tur: hit.slug });
            }}
          />
          <p className="mt-3 text-stone-700">{DISCRIMINATION_NOTE}</p>
        </div>
      )}
    </div>
  );
}
