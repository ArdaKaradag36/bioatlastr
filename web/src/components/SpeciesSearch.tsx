"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { loadSpeciesIndex, loadTaxonNames } from "@/lib/data.client";
import { normalize } from "@/lib/text";
import type { SpeciesIndexEntry, TaxonNames } from "@/lib/types";

interface Props {
  placeholder?: string;
  size?: "sm" | "lg";
  /** Only suggest species of this family. */
  family?: string;
  /** Called instead of navigating to the species page. */
  onSelect?: (s: SpeciesIndexEntry) => void;
  autoFocus?: boolean;
}

const MAX_SUGGESTIONS = 8;

/** Rank: name starts with query (0) < a word starts with it (1) < contains (2). */
function matchRank(entry: SpeciesIndexEntry, q: string, names: TaxonNames | null): number {
  const fields = [entry.name, entry.tr, entry.ts ?? "", entry.en].map(normalize);
  let best = 99;
  // Turkish names of the genus / family ("meşe" finds Quercus species) rank below the species' own names
  const higher = [...(names?.genus[entry.genus] ?? []).map((x) => [x.n, 2] as const), ...(names?.family[entry.family] ?? []).map((x) => [x.n, 3] as const)];
  for (const [n, rk] of higher) {
    const f = normalize(n);
    if (f.startsWith(q) || f.split(/[\s-]+/).some((w) => w.startsWith(q))) best = Math.min(best, rk);
  }
  for (const f of fields) {
    if (!f) continue;
    if (f.startsWith(q)) best = Math.min(best, 0);
    else if (f.split(/[\s-]+/).some((w) => w.startsWith(q))) best = Math.min(best, 1);
    else if (f.includes(q)) best = Math.min(best, 2);
  }
  return best;
}

export default function SpeciesSearch({ placeholder, size = "lg", family, onSelect, autoFocus }: Props) {
  const router = useRouter();
  const listId = useId();
  const [index, setIndex] = useState<SpeciesIndexEntry[] | null>(null);
  const [taxonNames, setTaxonNames] = useState<TaxonNames | null>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [error, setError] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  const ensureLoaded = () => {
    if (!index) loadSpeciesIndex().then(setIndex).catch(() => setError(true));
    if (!taxonNames) loadTaxonNames().then(setTaxonNames).catch(() => undefined); // optional: search works without it
  };

  const suggestions = useMemo(() => {
    const q = normalize(query.trim());
    if (!index || q.length < 1) return [];
    return index
      .filter((s) => !family || s.family === family)
      .map((s) => ({ s, r: matchRank(s, q, taxonNames) }))
      .filter((x) => x.r < 99)
      .sort((a, b) => a.r - b.r || a.s.name.localeCompare(b.s.name))
      .slice(0, MAX_SUGGESTIONS)
      .map((x) => x.s);
  }, [index, query, family, taxonNames]);

  // close when clicking outside
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  const choose = (s: SpeciesIndexEntry) => {
    setOpen(false);
    setQuery("");
    if (onSelect) onSelect(s);
    else router.push(`/turler/${s.slug}`);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((a) => Math.min(a + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter" && suggestions[active]) {
      e.preventDefault();
      choose(suggestions[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const inputClass =
    size === "lg"
      ? "w-full rounded-2xl border border-stone-300 bg-white px-5 py-4 text-lg shadow-sm"
      : "w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm";

  return (
    <div ref={box} className="relative w-full">
      <input
        type="search"
        role="combobox"
        aria-expanded={open && suggestions.length > 0}
        aria-controls={listId}
        aria-autocomplete="list"
        autoFocus={autoFocus}
        autoComplete="off"
        value={query}
        placeholder={placeholder ?? "Tür adı yazın…"}
        className={`${inputClass} outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200`}
        onFocus={() => {
          ensureLoaded();
          setOpen(true);
        }}
        onChange={(e) => {
          ensureLoaded();
          setQuery(e.target.value);
          setActive(0);
          setOpen(true);
        }}
        onKeyDown={onKeyDown}
      />
      {open && query.trim() !== "" && (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 z-50 mt-1 max-h-96 overflow-auto rounded-xl border border-stone-200 bg-white py-1 shadow-lg"
        >
          {error && <li className="px-3 py-2 text-sm text-red-600">Tür listesi yüklenemedi.</li>}
          {!error && !index && <li className="px-3 py-2 text-sm text-stone-500">Yükleniyor…</li>}
          {index && suggestions.length === 0 && (
            <li className="px-3 py-2 text-sm text-stone-500">Eşleşen tür bulunamadı.</li>
          )}
          {suggestions.map((s, i) => (
            <li
              key={s.slug}
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                choose(s);
              }}
              className={`cursor-pointer px-3 py-2 ${i === active ? "bg-emerald-50" : ""}`}
            >
              <div className="text-sm font-medium italic text-stone-900">{s.name}</div>
              <div className="text-xs text-stone-500">
                {[s.tr, s.en].filter(Boolean).join(" · ") || "Ortak ad yok"} · {s.family}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
