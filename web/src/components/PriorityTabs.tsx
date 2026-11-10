"use client";

import { useState } from "react";
import PriorityTable, { type PriorityRow } from "./PriorityTable";

const TABS = [
  { id: "top100", label: "İlk 100 (tavanlı)" },
  { id: "perFamily", label: "Aile başına 3" },
  { id: "empty", label: "Boş cinslerin ilki" },
  { id: "treeGain", label: "Ağaç kazancı" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function PriorityTabs({
  top100,
  perFamily,
  emptyGenera,
  treeGain,
}: {
  top100: PriorityRow[];
  perFamily: PriorityRow[];
  emptyGenera: PriorityRow[];
  treeGain: PriorityRow[];
}) {
  const [tab, setTab] = useState<TabId>("top100");

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Öncelik listeleri">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`min-h-11 rounded-xl px-4 text-sm font-semibold ${
              tab === t.id ? "bg-forest text-on-dark" : "border border-stone-300 bg-white text-stone-800 hover:bg-stone-50"
            }`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "top100" ? (
        <PriorityTable rows={top100} csvHref="/data/priority_species_top100.csv" />
      ) : null}
      {tab === "perFamily" ? (
        <div className="space-y-3">
          <p className="text-sm text-stone-700">
            Boşluğu olan her aileden en yüksek puanlı en fazla 3 tür (çeşitlilik için; tavanlı ilk 100’den bağımsız).
          </p>
          <PriorityTable rows={perFamily} />
        </div>
      ) : null}
      {tab === "empty" ? (
        <div className="space-y-3">
          <p className="text-sm text-stone-700">
            Hiçbir barkod dizisi olmayan her cinsten en yüksek puanlı bir tür — o cinste ilk dizi olur.
          </p>
          <PriorityTable rows={emptyGenera} />
        </div>
      ) : null}
      {tab === "treeGain" ? (
        <div className="space-y-3">
          <p className="text-sm text-stone-700">
            Zaten en az bir dizisi olan cinsler: kazanç = o cinsteki boşluk türü sayısı. Yeni dizi mevcut karşılaştırmaya eklenir.
          </p>
          <PriorityTable rows={treeGain} showGain />
        </div>
      ) : null}
    </div>
  );
}
