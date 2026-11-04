"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Bar } from "./ui";
import { loadSpeciesIndex } from "@/lib/data.client";
import { num, pct } from "@/lib/format";
import { normalize } from "@/lib/text";
import type { GenusRow, SpeciesIndexEntry } from "@/lib/types";

const select = "rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm";
const PAGE = 25;

function Pager({ page, pages, setPage }: { page: number; pages: number; setPage: (n: number) => void }) {
  return (
    <div className="mt-3 flex items-center justify-between text-sm">
      <button className="rounded-lg border border-stone-300 px-3 py-1.5 disabled:opacity-40" disabled={page === 0} onClick={() => setPage(page - 1)}>
        ← Önceki
      </button>
      <span className="text-stone-600">Sayfa {page + 1} / {pages}</span>
      <button className="rounded-lg border border-stone-300 px-3 py-1.5 disabled:opacity-40" disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>
        Sonraki →
      </button>
    </div>
  );
}

/** Genera ordered by how little barcode data they have. */
export function GeneraTable({ genera, families, markers }: { genera: GenusRow[]; families: string[]; markers: string[] }) {
  const [family, setFamilyRaw] = useState("");
  const [minSpecies, setMinSpeciesRaw] = useState(1);
  const [sort, setSortRaw] = useState<"share" | "missing">("share");
  const [page, setPage] = useState(0);
  const setFamily = (v: string) => { setFamilyRaw(v); setPage(0); };
  const setMinSpecies = (v: number) => { setMinSpeciesRaw(v); setPage(0); };
  const setSort = (v: "share" | "missing") => { setSortRaw(v); setPage(0); };

  const rows = useMemo(() => {
    const list = genera.filter((g) => (!family || g.family === family) && g.species >= minSpecies);
    list.sort((a, b) =>
      sort === "missing"
        ? b.species_without_any - a.species_without_any || a.genus.localeCompare(b.genus)
        : a.species_with_any / a.species - b.species_with_any / b.species ||
          b.species - a.species ||
          a.genus.localeCompare(b.genus),
    );
    return list;
  }, [genera, family, minSpecies, sort]);

  const pages = Math.max(1, Math.ceil(rows.length / PAGE));

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <select className={select} value={family} onChange={(e) => setFamily(e.target.value)} aria-label="Aile">
          <option value="">Tüm aileler</option>
          {families.map((f) => <option key={f}>{f}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm">
          En az tür sayısı
          <input type="number" min={1} value={minSpecies} onChange={(e) => setMinSpecies(Math.max(1, Number(e.target.value) || 1))} className={`${select} w-20`} />
        </label>
        <select className={select} value={sort} onChange={(e) => setSort(e.target.value as "share" | "missing")} aria-label="Sıralama">
          <option value="share">Sırala: dizisi olan tür oranı (en düşük)</option>
          <option value="missing">Sırala: dizisi olmayan tür sayısı (en çok)</option>
        </select>
        <span className="ml-auto text-sm text-stone-500">{num(rows.length)} cins</span>
      </div>
      <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="p-3">Cins</th>
              <th className="hidden p-3 sm:table-cell">Aile</th>
              <th className="p-3 text-right">Tür</th>
              <th className="p-3">Dizisi olan tür</th>
              {markers.map((m) => <th key={m} className="hidden p-3 text-right md:table-cell">{m}</th>)}
              <th className="p-3 text-right">Toplam dizi</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(page * PAGE, (page + 1) * PAGE).map((g) => (
              <tr key={`${g.family}-${g.genus}`} className="border-t border-stone-100">
                <td className="p-3 font-medium italic">{g.genus}</td>
                <td className="hidden p-3 sm:table-cell">{g.family}</td>
                <td className="p-3 text-right">{num(g.species)}</td>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24"><Bar value={g.species_with_any} max={g.species} /></div>
                    <span className="whitespace-nowrap text-xs text-stone-600">
                      {num(g.species_with_any)} ({pct(g.species_with_any / g.species, 0)})
                    </span>
                  </div>
                </td>
                {markers.map((m) => (
                  <td key={m} className="hidden p-3 text-right md:table-cell">{num(Number(g[`species_${m}`]))}</td>
                ))}
                <td className="p-3 text-right">{num(g.sequences)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pager page={page} pages={pages} setPage={setPage} />
    </div>
  );
}

/** Species that have no sequence at all (or none for a chosen marker). */
export function MissingSpeciesTable({ families, markers, initialEndemic = false }: { families: string[]; markers: string[]; initialEndemic?: boolean }) {
  const [endemicOnly, setEndemicOnly] = useState(initialEndemic);
  const [index, setIndex] = useState<SpeciesIndexEntry[] | null>(null);
  const [family, setFamilyRaw] = useState("");
  const [marker, setMarkerRaw] = useState(""); // "" = no marker at all
  const [text, setTextRaw] = useState("");
  const [page, setPage] = useState(0);
  const setFamily = (v: string) => { setFamilyRaw(v); setPage(0); };
  const setMarker = (v: string) => { setMarkerRaw(v); setPage(0); };
  const setText = (v: string) => { setTextRaw(v); setPage(0); };

  useEffect(() => {
    loadSpeciesIndex().then(setIndex);
  }, []);

  const rows = useMemo(() => {
    if (!index) return [];
    const q = normalize(text.trim());
    return index.filter((s) => {
      if (family && s.family !== family) return false;
      if (endemicOnly && s.endemic !== 1) return false;
      const missing = marker ? s.counts[marker] === 0 : markers.every((m) => s.counts[m] === 0);
      if (!missing) return false;
      return !q || [s.name, s.tr, s.ts ?? "", s.en].some((f) => normalize(f).includes(q));
    });
  }, [index, family, marker, text, markers, endemicOnly]);

  const pages = Math.max(1, Math.ceil(rows.length / PAGE));

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <input type="search" value={text} onChange={(e) => setText(e.target.value)} placeholder="Filtrele…" className={`${select} w-48`} />
        <select className={select} value={family} onChange={(e) => setFamily(e.target.value)} aria-label="Aile">
          <option value="">Tüm aileler</option>
          {families.map((f) => <option key={f}>{f}</option>)}
        </select>
        <select className={select} value={marker} onChange={(e) => setMarker(e.target.value)} aria-label="Eksik marker">
          <option value="">Hiçbir markerde dizisi yok</option>
          {markers.map((m) => <option key={m} value={m}>{m} dizisi yok</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={endemicOnly} onChange={(e) => { setEndemicOnly(e.target.checked); setPage(0); }} />
          Yalnızca endemikler
        </label>
        <span className="ml-auto text-sm text-stone-500">{index ? `${num(rows.length)} tür` : "Yükleniyor…"}</span>
      </div>
      <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr><th className="p-3">Tür</th><th className="hidden p-3 sm:table-cell">Türkçe ad</th><th className="p-3">Aile</th><th className="p-3">Endemik</th></tr>
          </thead>
          <tbody>
            {rows.slice(page * PAGE, (page + 1) * PAGE).map((s) => (
              <tr key={s.slug} className="border-t border-stone-100">
                <td className="p-3"><Link href={`/turler/${s.slug}`} className="italic text-emerald-800 hover:underline">{s.name}</Link></td>
                <td className="hidden p-3 text-stone-600 sm:table-cell">{s.tr || "—"}</td>
                <td className="p-3">{s.family}</td>
                <td className="p-3">{s.endemic === 1 ? "evet" : ""}</td>
              </tr>
            ))}
            {index && rows.length === 0 && <tr><td colSpan={4} className="p-4 text-stone-500">Bu filtreyle eksik tür yok.</td></tr>}
          </tbody>
        </table>
      </div>
      <Pager page={page} pages={pages} setPage={setPage} />
    </div>
  );
}
