"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { publicUrl } from "@/lib/site";
import { slugify } from "@/lib/text";

export type PriorityRow = {
  rank: number;
  species: string;
  family: string;
  genus: string;
  endemic: number;
  n_wcvp_areas: number;
  endemism: number;
  range_restriction: number;
  genus_gap: number;
  phylogenetic_usefulness: number;
  family_gap: number;
  total_score: number;
  neden_bu_tur: string;
};

type SortKey = keyof Pick<
  PriorityRow,
  | "rank"
  | "species"
  | "family"
  | "genus"
  | "endemism"
  | "range_restriction"
  | "genus_gap"
  | "phylogenetic_usefulness"
  | "family_gap"
  | "total_score"
  | "n_wcvp_areas"
>;

function fmt(n: number): string {
  return n.toFixed(2);
}

export default function PriorityTable({ rows }: { rows: PriorityRow[] }) {
  const [key, setKey] = useState<SortKey>("rank");
  const [asc, setAsc] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      let cmp = 0;
      if (typeof av === "string" && typeof bv === "string") cmp = av.localeCompare(bv, "tr");
      else cmp = Number(av) - Number(bv);
      return asc ? cmp : -cmp;
    });
    return copy;
  }, [rows, key, asc]);

  function toggle(next: SortKey) {
    if (key === next) setAsc(!asc);
    else {
      setKey(next);
      setAsc(next === "rank" || next === "species" || next === "family" || next === "genus");
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
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <a
          className="inline-flex min-h-11 items-center rounded-xl bg-forest px-4 font-semibold text-on-dark hover:bg-forest-2"
          href={publicUrl("/data/priority_species_top100.csv")}
          download
        >
          CSV indir (ilk 100)
        </a>
        <span className="text-stone-600">Sütun başlığına tıklayınca sıralama değişir.</span>
      </div>
      <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white shadow-card">
        <table className="min-w-full text-sm">
          <thead className="border-b border-stone-200 bg-stone-50">
            <tr>
              {head("rank", "Sıra")}
              {head("species", "Tür")}
              {head("family", "Aile")}
              {head("genus", "Cins")}
              {head("n_wcvp_areas", "WCVP alan")}
              {head("endemism", "Endemizm")}
              {head("range_restriction", "Dar yayılış")}
              {head("genus_gap", "Cins boşluğu")}
              {head("phylogenetic_usefulness", "Filogenetik yarar")}
              {head("family_gap", "Aile boşluğu")}
              {head("total_score", "Toplam")}
              <th className="p-2 text-left font-semibold text-stone-700">Neden bu tür?</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.species} className="border-b border-stone-100 align-top odd:bg-white even:bg-stone-50/60">
                <td className="p-2 tabular-nums text-stone-700">{r.rank}</td>
                <td className="p-2">
                  <Link className="font-medium italic text-link underline" href={`/turler/${slugify(r.species)}`}>
                    {r.species}
                  </Link>
                  {r.endemic === 1 ? <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-800">endemik</span> : null}
                </td>
                <td className="p-2 text-stone-700">{r.family}</td>
                <td className="p-2 italic text-stone-700">{r.genus}</td>
                <td className="p-2 tabular-nums">{r.n_wcvp_areas}</td>
                <td className="p-2 tabular-nums">{fmt(r.endemism)}</td>
                <td className="p-2 tabular-nums">{fmt(r.range_restriction)}</td>
                <td className="p-2 tabular-nums">{fmt(r.genus_gap)}</td>
                <td className="p-2 tabular-nums">{fmt(r.phylogenetic_usefulness)}</td>
                <td className="p-2 tabular-nums">{fmt(r.family_gap)}</td>
                <td className="p-2 tabular-nums font-semibold">{fmt(r.total_score)}</td>
                <td className="max-w-sm p-2 text-stone-700">{r.neden_bu_tur}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
