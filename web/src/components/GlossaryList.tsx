"use client";

import { useMemo, useState } from "react";
import { GLOSSARY, type GlossaryGroup } from "@/lib/glossary";
import { normalize } from "@/lib/text";

const GROUPS: GlossaryGroup[] = ["DNA ve barkod", "Barkod bölgeleri", "Diziler ve veri kaynakları", "Mesafe ve ağaç", "Bitki sınıflandırması", "Sonuçları okumak"];

export default function GlossaryList() {
  const [q, setQ] = useState("");
  const items = useMemo(() => {
    const n = normalize(q.trim());
    if (!n) return GLOSSARY;
    return GLOSSARY.filter((g) => normalize([g.term, g.aka ?? "", g.short, g.more ?? ""].join(" ")).includes(n));
  }, [q]);

  return (
    <div>
      <label htmlFor="sozluk-ara" className="mb-1 block font-medium text-stone-800">Sözlükte ara</label>
      <input
        id="sozluk-ara"
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="örneğin: mesafe, rbcL, endemik…"
        className="w-full max-w-md rounded-xl border border-stone-300 bg-white px-4 py-3 text-base"
      />
      <p className="mt-2 text-sm text-stone-600" aria-live="polite">{items.length} terim gösteriliyor.</p>

      <nav aria-label="Terim dizini" className="my-6 flex flex-wrap gap-2">
        {items.map((g) => (
          <a key={g.id} href={`#${g.id}`} className="rounded-full border border-stone-200 bg-white px-3 py-1.5 text-sm text-link hover:bg-emerald-50">{g.term}</a>
        ))}
      </nav>

      {GROUPS.map((grp) => {
        const list = items.filter((g) => g.group === grp);
        if (list.length === 0) return null;
        return (
          <section key={grp} aria-labelledby={`grp-${grp}`} className="mb-10">
            <h2 id={`grp-${grp}`} className="mb-4 text-2xl font-semibold">{grp}</h2>
            <dl className="grid gap-4 md:grid-cols-2">
              {list.map((g) => (
                <div key={g.id} id={g.id} className="scroll-mt-24 rounded-2xl border border-stone-200 bg-white p-5 shadow-card target:ring-2 target:ring-accent">
                  <dt className="font-serif text-xl font-semibold text-stone-900">{g.term}</dt>
                  <dd className="mt-1 text-stone-800">
                    <p>{g.short}</p>
                    {g.more && <p className="mt-2 text-stone-700">{g.more}</p>}
                    {g.analogy && (
                      <p className="mt-2 rounded-lg bg-accent-soft p-3 text-sm text-stone-800"><strong>Günlük hayattan: </strong>{g.analogy}</p>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        );
      })}
      {items.length === 0 && <p className="text-stone-700">Eşleşen terim bulunamadı. Başka bir sözcük deneyin.</p>}
    </div>
  );
}
