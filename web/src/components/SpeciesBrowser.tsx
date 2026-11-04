"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import SpeciesSearch from "./SpeciesSearch";
import Term from "./Term";
import { loadSpeciesIndex } from "@/lib/data.client";
import { num } from "@/lib/format";
import { normalize } from "@/lib/text";
import type { SpeciesIndexEntry } from "@/lib/types";

const PAGE_SIZE = 50;

export default function SpeciesBrowser({ families, markers }: { families: string[]; markers: string[] }) {
  const [index, setIndex] = useState<SpeciesIndexEntry[] | null>(null);
  const [family, setFamilyRaw] = useState("");
  const [marker, setMarkerRaw] = useState(""); // "" = any
  const [onlyWith, setOnlyWithRaw] = useState(false);
  const [filterText, setFilterTextRaw] = useState("");
  const [page, setPage] = useState(0);
  // every filter change goes back to the first page
  const setFamily = (v: string) => { setFamilyRaw(v); setPage(0); };
  const setMarker = (v: string) => { setMarkerRaw(v); setPage(0); };
  const setOnlyWith = (v: boolean) => { setOnlyWithRaw(v); setPage(0); };
  const setFilterText = (v: string) => { setFilterTextRaw(v); setPage(0); };

  useEffect(() => {
    loadSpeciesIndex().then(setIndex);
  }, []);

  const filtered = useMemo(() => {
    if (!index) return [];
    const q = normalize(filterText.trim());
    return index.filter((s) => {
      if (family && s.family !== family) return false;
      if (onlyWith) {
        const has = marker ? s.counts[marker] > 0 : markers.some((m) => s.counts[m] > 0);
        if (!has) return false;
      }
      if (q && ![s.name, s.tr, s.ts ?? "", s.en].some((f) => normalize(f).includes(q))) return false;
      return true;
    });
  }, [index, family, marker, onlyWith, filterText, markers]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const rows = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const select = "min-h-11 rounded-lg border border-stone-300 bg-white px-3 py-2 text-base";

  return (
    <div>
      <SpeciesSearch placeholder="Tür ara: Latince veya Türkçe ad (ör. Quercus, meşe)" />

      <h2 className="mb-3 mt-10 text-2xl font-semibold">Tüm türler</h2>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          type="search"
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          placeholder="Listede filtrele…"
          aria-label="Listede filtrele"
          className={`${select} w-full md:w-56`}
        />
        <select className={select} value={marker} onChange={(e) => setMarker(e.target.value)} aria-label="Barkod bölgesi">
          <option value="">Herhangi bir barkod bölgesi</option>
          {markers.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
        <select
          className={`${select} md:hidden`}
          value={onlyWith ? "with" : "any"}
          onChange={(e) => setOnlyWith(e.target.value === "with")}
          aria-label="Kayıtlı / eksik"
        >
          <option value="any">Kayıtlı veya eksik</option>
          <option value="with">Yalnızca kayıtlı</option>
        </select>
        <details className="w-full md:hidden">
          <summary className="flex min-h-11 cursor-pointer list-none items-center rounded-lg border border-stone-300 bg-white px-3 font-medium">
            Filtrele
          </summary>
          <div className="mt-2 flex flex-col gap-2">
            <select className={select} value={family} onChange={(e) => setFamily(e.target.value)} aria-label="Aile">
              <option value="">Tüm aileler</option>
              {families.map((f) => (
                <option key={f}>{f}</option>
              ))}
            </select>
          </div>
        </details>
        <select className={`${select} hidden md:inline`} value={family} onChange={(e) => setFamily(e.target.value)} aria-label="Aile">
          <option value="">Tüm aileler</option>
          {families.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
        <label className="hidden min-h-11 items-center gap-2 md:flex">
          <input type="checkbox" className="h-5 w-5" checked={onlyWith} onChange={(e) => setOnlyWith(e.target.checked)} />
          Yalnızca dizisi olanlar
        </label>
        <span className="ml-auto text-sm text-stone-600" aria-live="polite">{index ? `${num(filtered.length)} tür` : "Yükleniyor…"}</span>
      </div>

      <ul className="space-y-3 md:hidden">
        {rows.map((s) => {
          const nAny = markers.reduce((n, m) => n + (s.counts[m] ?? 0), 0);
          return (
            <li key={s.slug} className="rounded-2xl border border-stone-200 bg-white p-4">
              <Link href={`/turler/${s.slug}`} className="block min-h-11 italic text-link underline">{s.name}</Link>
              <p className="mt-1 text-sm text-stone-700">{s.family}{s.tr ? ` · ${s.tr}` : ""}</p>
              <p className="mt-1 text-sm text-stone-600">{nAny > 0 ? `${nAny} dizi` : "kayıt yok"}</p>
            </li>
          );
        })}
        {index && rows.length === 0 && <li className="text-stone-600">Sonuç yok.</li>}
      </ul>

      <div tabIndex={0} className="hidden overflow-x-auto rounded-xl border border-stone-200 bg-white md:block">
        <table className="w-full text-[0.95rem]">
          <caption className="sr-only">Türler, aileleri ve barkod bölgesi başına dizi sayıları</caption>
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th scope="col" className="p-3">Tür <span className="font-normal">(<Term id="latince-ad">Latince ad</Term>)</span></th>
              <th scope="col" className="hidden p-3 sm:table-cell"><Term id="halk-adi">Halk adı</Term></th>
              <th scope="col" className="hidden p-3 md:table-cell"><Term id="familya">Aile</Term></th>
              {markers.map((m) => (
                <th scope="col" key={m} className="p-3 text-center">{m} <span className="sr-only">dizi sayısı</span></th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.slug} className="border-t border-stone-100 hover:bg-stone-50">
                <td className="p-3">
                  <Link href={`/turler/${s.slug}`} className="italic text-link hover:underline">{s.name}</Link>
                </td>
                <td className="hidden p-3 text-stone-600 sm:table-cell">{[s.tr, s.en].filter(Boolean).join(" · ") || "—"}</td>
                <td className="hidden p-3 md:table-cell">{s.family}</td>
                {markers.map((m) => (
                  <td key={m} className="p-3 text-center">
                    <span className={s.counts[m] > 0 ? "font-semibold text-link" : "text-stone-500"}>{s.counts[m]}</span>
                  </td>
                ))}
              </tr>
            ))}
            {index && rows.length === 0 && (
              <tr><td className="p-4 text-stone-600" colSpan={3 + markers.length}>Sonuç yok.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <button className="min-h-11 rounded-lg border border-stone-300 bg-white px-4 py-2 disabled:opacity-40" disabled={page === 0} onClick={() => setPage(page - 1)}>
          ← Önceki
        </button>
        <span className="text-stone-600">Sayfa {page + 1} / {pages}</span>
        <button className="min-h-11 rounded-lg border border-stone-300 bg-white px-4 py-2 disabled:opacity-40" disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>
          Sonraki →
        </button>
      </div>
    </div>
  );
}
