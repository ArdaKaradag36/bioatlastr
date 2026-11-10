"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { publicUrl } from "@/lib/site";
import { slugify } from "@/lib/text";

export type PriorityRow = {
  rank?: number;
  gain_rank?: number;
  family_pick_rank?: number;
  species: string;
  family: string;
  genus: string;
  endemic: number;
  n_wcvp_areas: number;
  n_wcvp_regions?: number;
  genus_n_with_any?: number;
  genus_n_gap?: number;
  tree_gain?: number;
  endemism: number;
  range_restriction: number;
  genus_gap: number;
  phylogenetic_usefulness: number;
  family_gap: number;
  total_score: number;
  tie_group?: number;
  tie_group_size?: number;
  robust_core?: number;
  neden_bu_tur: string;
};

type SortKey = keyof PriorityRow;

function fmt(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(2);
}

export default function PriorityTable({
  rows,
  csvHref,
  showGain = false,
}: {
  rows: PriorityRow[];
  csvHref?: string;
  showGain?: boolean;
}) {
  const [key, setKey] = useState<SortKey>(showGain ? "gain_rank" : "rank");
  const [asc, setAsc] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      let cmp = 0;
      if (typeof av === "string" && typeof bv === "string") cmp = av.localeCompare(bv, "tr");
      else cmp = Number(av ?? 0) - Number(bv ?? 0);
      return asc ? cmp : -cmp;
    });
    return copy;
  }, [rows, key, asc]);

  function toggle(next: SortKey) {
    if (key === next) setAsc(!asc);
    else {
      setKey(next);
      setAsc(next === "rank" || next === "species" || next === "family" || next === "genus" || next === "gain_rank");
    }
  }

  const head = (id: SortKey, label: string) => (
    <th className="cursor-pointer whitespace-nowrap p-2 text-left font-semibold text-stone-700" onClick={() => toggle(id)}>
      {label}
      {key === id ? (asc ? " ↑" : " ↓") : ""}
    </th>
  );

  return (
    <div className="space-y-3">
      {csvHref ? (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <a
            className="inline-flex min-h-11 items-center rounded-xl bg-forest px-4 font-semibold text-on-dark hover:bg-forest-2"
            href={publicUrl(csvHref)}
            download
          >
            CSV indir
          </a>
          <span className="text-stone-600">Sütun başlığına tıklayınca sıralama değişir. “Çekirdek” = tüm ağırlık kümelerinde ilk 100’de.</span>
        </div>
      ) : null}
      <div tabIndex={0} className="overflow-x-auto rounded-2xl border border-stone-200 bg-white shadow-card">
        <table className="min-w-full text-sm">
          <thead className="border-b border-stone-200 bg-stone-50">
            <tr>
              {showGain ? head("gain_rank", "Kazanç sırası") : head("rank", "Sıra")}
              {head("species", "Tür")}
              {head("family", "Aile")}
              {head("genus", "Cins")}
              {head("n_wcvp_areas", "Alan")}
              {showGain ? head("tree_gain", "Ağaç kazancı") : null}
              {head("total_score", "Toplam")}
              {head("robust_core", "Çekirdek")}
              {head("tie_group_size", "Eşitlik")}
              <th className="p-2 text-left font-semibold text-stone-700">Neden bu tür?</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={`${r.genus}-${r.species}`} className="border-b border-stone-100 align-top odd:bg-white even:bg-stone-50/60">
                <td className="p-2 tabular-nums text-stone-700">{showGain ? r.gain_rank : r.rank}</td>
                <td className="p-2">
                  <Link className="font-medium italic text-link underline" href={`/turler/${slugify(r.species)}`}>
                    {r.species}
                  </Link>
                  {r.endemic === 1 ? <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-800">endemik</span> : null}
                </td>
                <td className="p-2 text-stone-700">{r.family}</td>
                <td className="p-2 italic text-stone-700">{r.genus}</td>
                <td className="p-2 tabular-nums">{r.n_wcvp_areas}{r.n_wcvp_regions != null ? ` / ${r.n_wcvp_regions}` : ""}</td>
                {showGain ? <td className="p-2 tabular-nums">{r.tree_gain ?? "—"}</td> : null}
                <td className="p-2 tabular-nums font-semibold">{fmt(r.total_score)}</td>
                <td className="p-2">{r.robust_core === 1 ? "evet" : ""}</td>
                <td className="p-2 tabular-nums">{(r.tie_group_size ?? 1) > 1 ? r.tie_group_size : ""}</td>
                <td className="max-w-sm p-2 text-stone-700">{r.neden_bu_tur}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
