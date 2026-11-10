import type { Metadata } from "next";
import Link from "next/link";
import fs from "node:fs";
import path from "node:path";
import PriorityTabs from "@/components/PriorityTabs";
import type { PriorityRow } from "@/components/PriorityTable";
import Term from "@/components/Term";
import { Callout, Card, PageIntro, PageTitle, Purpose } from "@/components/ui";
import { num, pct } from "@/lib/format";

export const metadata: Metadata = {
  title: "Öncelik listesi",
  description:
    "ENA/INSDC’de henüz kullanılabilir barkodu olmayan türler için açık veriyle hesaplanmış dizileme öncelik listeleri (skorlar, cins/aile tavanları).",
};

type SensPair = {
  set_a: string;
  set_b: string;
  capped_overlap_count: number;
  capped_overlap_fraction: number;
  spearman_full_scores: number | null;
  robust_core_size: number;
};

type PriorityPayload = {
  gap_rule: { required_markers: string[] };
  weights: Record<string, number>;
  caps: { max_per_genus: number; max_per_family: number; top_n: number };
  notes: Record<string, string>;
  diagnosis: {
    tied_at_max_score: number;
    saturating_components?: string[];
    robust_core_size: number;
    top100_genera: number;
    top100_families: number;
    top100_endemic: number;
    remaining_ties_in_top100: number;
    n_gaps: number;
  };
  sensitivity_summary: { robust_core_size: number; pairs: SensPair[] };
  n_scored_gaps?: number;
  n_species_total?: number;
  lists: {
    top100: PriorityRow[];
    top_per_family: PriorityRow[];
    empty_genera: PriorityRow[];
    tree_gain: PriorityRow[];
  };
};

function loadPriority(): PriorityPayload {
  const full = path.join(process.cwd(), "public", "data", "priority_top100.json");
  return JSON.parse(fs.readFileSync(full, "utf-8")) as PriorityPayload;
}

export default function PriorityPage() {
  const data = loadPriority();
  const w = data.weights;
  const caps = data.caps;
  const markers = data.gap_rule.required_markers.join(" + ");
  const d = data.diagnosis;
  const pairs = (data.sensitivity_summary?.pairs ?? []).filter((p) => p.set_a === "default" && p.set_b !== "default");

  return (
    <div>
      <PageTitle eyebrow="Öncelik listesi" title="İlk 100: hangi türler önce dizilensin?">
        Veri boşluklarından sürekli puanlarla üretilmiş, cins/aile tavanlı öneri listesi. Uzman kararının yerini tutmaz.
      </PageTitle>
      <PageIntro
        what={
          <p>
            ENA/INSDC’de henüz kullanılabilir barkodu olmayan türler arasından açık veriyle hesaplanan sıralama.
            Liste bir <Term id="veri-boslugu">veri boşluğu</Term> önerisidir; tehdit veya örnek bulunabilirliği burada yoktur.
          </p>
        }
        how={
          <p>
            Bileşenler 0–1 arasıdır (çoğu yüzdelik / log ölçekli). İlk {num(caps.top_n)} tür, skor sırasıyla seçilir ama
            cins başına en fazla {num(caps.max_per_genus)}, aile başına en fazla {num(caps.max_per_family)} tür alınır.
            Eşit skorlarda alfabetik sıra kullanılmaz; dizili akraba sayısı ve WCVP alan sayısı kırar.
          </p>
        }
      />

      <Callout tone="warn">
        <strong>Öneri / sınırlar:</strong> Bu liste yalnızca WCVP yayılışı ve ENA/INSDC barkod sayılarından üretilir (IUCN yok).
        Aynı puana düşen türler <em>tie_group</em> ile işaretlenir; kalan eşitlikler tavanlardan sonra da olabilir.
        Ağırlıklar ve tavanlar yapılandırmadadır — biyolog ayarlamalıdır. Liste uzman yargısının yerine geçmez.
      </Callout>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className="text-sm font-semibold text-stone-600">Skorlanan boşluk</div>
          <div className="font-serif text-3xl font-bold text-link">{num(data.n_scored_gaps ?? d.n_gaps)}</div>
          <p className="mt-2 text-sm text-stone-700">Kural: {markers} yok{data.n_species_total ? ` / ${num(data.n_species_total)} tür` : ""}.</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">İlk 100 çeşitlilik</div>
          <div className="font-serif text-3xl font-bold text-link">{num(d.top100_genera)} / {num(d.top100_families)}</div>
          <p className="mt-2 text-sm text-stone-700">Cins / aile (tavan: {num(caps.max_per_genus)} / {num(caps.max_per_family)}).</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Endemik / çekirdek</div>
          <div className="font-serif text-3xl font-bold text-red-800">{num(d.top100_endemic)} / {num(d.robust_core_size)}</div>
          <p className="mt-2 text-sm text-stone-700">Endemik sayısı · tüm ağırlık kümelerinde ilk 100’de kalan tür.</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Kalan eşitlik</div>
          <div className="font-serif text-3xl font-bold text-link">{num(d.remaining_ties_in_top100)}</div>
          <p className="mt-2 text-sm text-stone-700">Tavanlı listede tie_group_size &gt; 1 olan satır.</p>
        </Card>
      </div>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Puan nasıl hesaplanır?</h2>
        <ul className="max-w-3xl list-disc space-y-1 pl-5 text-stone-800">
          <li><strong>Endemizm</strong> ({pct(w.endemism)}): WCVP’ye göre yalnızca Türkiye → 1 / 0.</li>
          <li>
            <strong>Dar yayılış</strong> ({pct(w.range_restriction)}): TDWG düzey-3 alan + düzey-2 bölge sayılarının
            tersinin boşluk havuzundaki yüzdelik sırası (WCVP’de düzey-4 yok).
          </li>
          <li>
            <strong>Cins açığı</strong> ({pct(w.genus_gap)}): Boşluk oranı ile mutlak boşluk sayısının yüzdeliklerinin ortalaması.
          </li>
          <li>
            <strong>Filogenetik yarar</strong> ({pct(w.phylogenetic_usefulness)}): log(1 + dizili akraba) / log(1 + max).
          </li>
          <li>
            <strong>Aile açığı</strong> ({pct(w.family_gap)}): Aile boşluk oranı ve mutlak sayının yüzdelikleri.
          </li>
        </ul>
        <p className="max-w-3xl text-sm text-stone-700">{data.notes?.tree_gain}</p>
      </section>

      {pairs.length > 0 ? (
        <section className="mt-8 space-y-2">
          <h2 className="font-serif text-xl font-bold text-stone-900">Ağırlık duyarlılığı (tavanlı ilk 100)</h2>
          <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
            <table className="min-w-full text-sm">
              <thead className="bg-stone-50 text-left">
                <tr>
                  <th className="p-2">Küme</th>
                  <th className="p-2">Örtüşme</th>
                  <th className="p-2">Spearman (tüm boşluklar)</th>
                </tr>
              </thead>
              <tbody>
                {pairs.map((p) => (
                  <tr key={p.set_b} className="border-t border-stone-100">
                    <td className="p-2">{p.set_b}</td>
                    <td className="p-2 tabular-nums">{p.capped_overlap_count} / {caps.top_n} ({pct(p.capped_overlap_fraction)})</td>
                    <td className="p-2 tabular-nums">{p.spearman_full_scores ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-sm text-stone-600">
            Sağlam çekirdek (tüm kümelerde ilk 100): {num(data.sensitivity_summary.robust_core_size)} tür.
            Ayrıntı: <code className="rounded bg-stone-100 px-1">results/priority_sensitivity.csv</code>.
          </p>
        </section>
      ) : null}

      <section className="mt-10">
        <h2 className="mb-4 font-serif text-2xl font-bold text-stone-900">Listeler</h2>
        <PriorityTabs
          top100={data.lists.top100}
          perFamily={data.lists.top_per_family}
          emptyGenera={data.lists.empty_genera}
          treeGain={data.lists.tree_gain}
        />
      </section>

      <p className="mt-6 text-sm text-stone-600">
        <Link className="text-link underline" href="/veri-bosluklari">Veri boşlukları</Link>
        {" · "}
        <Link className="text-link underline" href="/yontem">Yöntem</Link>
        {" · "}
        <Link className="text-link underline" href="/sozluk">Sözlük</Link>
      </p>

      <Purpose>
        Sınırlı dizileme kaynağını şeffaf, çeşitlendirilmiş ve ağırlıklara kısmen dayanıklı bir öneriyle yönlendirmek.
      </Purpose>
    </div>
  );
}
