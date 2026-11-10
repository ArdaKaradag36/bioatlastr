"use client";

import { useMemo, useState } from "react";
import { num } from "@/lib/format";

export type FamilyGuideRow = {
  family: string;
  recommendation: string;
  n_species_behind: number;
  n_family_species: number;
  sentence: string;
  n_pairs: number;
  n_pairs_adequate: number;
  n_pairs_clear: number;
};

function badge(rec: string): string {
  if (rec === "yetersiz veri") return "bg-stone-100 text-stone-700";
  if (rec === "fark belirsiz") return "bg-amber-100 text-amber-900";
  return "bg-emerald-100 text-link";
}

export default function MarkerGuideTable({ rows }: { rows: FamilyGuideRow[] }) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "recommended" | "yetersiz" | "belirsiz">("all");

  const filtered = useMemo(() => {
    const needle = q.trim().toLocaleLowerCase("tr-TR");
    return rows.filter((r) => {
      if (filter === "recommended" && !["rbcL", "matK", "ITS"].includes(r.recommendation)) return false;
      if (filter === "yetersiz" && r.recommendation !== "yetersiz veri") return false;
      if (filter === "belirsiz" && r.recommendation !== "fark belirsiz") return false;
      if (!needle) return true;
      return r.family.toLocaleLowerCase("tr-TR").includes(needle) || r.sentence.toLocaleLowerCase("tr-TR").includes(needle);
    });
  }, [rows, q, filter]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        <label className="flex min-h-11 flex-1 items-center gap-2 rounded-xl border border-stone-300 bg-white px-3 text-sm">
          <span className="text-stone-600">Ara</span>
          <input
            className="min-w-0 flex-1 bg-transparent outline-none"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Aile adı…"
          />
        </label>
        <select
          className="min-h-11 rounded-xl border border-stone-300 bg-white px-3 text-sm"
          value={filter}
          onChange={(e) => setFilter(e.target.value as typeof filter)}
        >
          <option value="all">Tümü ({num(rows.length)})</option>
          <option value="recommended">Öneri var</option>
          <option value="belirsiz">Fark belirsiz</option>
          <option value="yetersiz">Yetersiz veri</option>
        </select>
      </div>
      <p className="text-sm text-stone-600">{num(filtered.length)} aile gösteriliyor.</p>
      <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white shadow-card">
        <table className="min-w-full text-sm">
          <thead className="border-b border-stone-200 bg-stone-50 text-left">
            <tr>
              <th className="p-3">Aile</th>
              <th className="p-3">Öneri</th>
              <th className="p-3">Ortak / aile türü</th>
              <th className="p-3">Açıklama</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={r.family} className="border-b border-stone-100 align-top odd:bg-white even:bg-stone-50/60">
                <td className="p-3 font-medium text-stone-900">{r.family}</td>
                <td className="p-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${badge(r.recommendation)}`}>
                    {r.recommendation}
                  </span>
                </td>
                <td className="p-3 tabular-nums text-stone-700">
                  {num(r.n_species_behind)} / {num(r.n_family_species)}
                </td>
                <td className="max-w-xl p-3 text-stone-700">{r.sentence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
