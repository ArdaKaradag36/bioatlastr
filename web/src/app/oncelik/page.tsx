import type { Metadata } from "next";
import Link from "next/link";
import fs from "node:fs";
import path from "node:path";
import PriorityTable, { type PriorityRow } from "@/components/PriorityTable";
import Term from "@/components/Term";
import { Callout, Card, PageIntro, PageTitle, Purpose } from "@/components/ui";
import { num, pct } from "@/lib/format";

export const metadata: Metadata = { title: "Öncelik listesi" };

type PriorityPayload = {
  gap_rule: { required_markers: string[] };
  weights: Record<string, number>;
  top_n: number;
  n_scored_gaps: number;
  n_species_total?: number;
  species: PriorityRow[];
};

function loadPriority(): PriorityPayload {
  const full = path.join(process.cwd(), "public", "data", "priority_top100.json");
  return JSON.parse(fs.readFileSync(full, "utf-8")) as PriorityPayload;
}

export default function PriorityPage() {
  const data = loadPriority();
  const w = data.weights;
  const markers = data.gap_rule.required_markers.join(" + ");
  const endemicN = data.species.filter((s) => s.endemic === 1).length;

  return (
    <div>
      <PageTitle eyebrow="Öncelik listesi" title="İlk 100: hangi türler önce dizilensin?">
        Veri boşluklarından, şeffaf bir puanla üretilmiş öneri listesi. Uzman kararının yerini tutmaz; saha ve laboratuvar planına yardımcı olmak içindir.
      </PageTitle>
      <PageIntro
        what={
          <p>
            ENA/INSDC’de henüz kullanılabilir barkodu olmayan türler arasından, açık veriyle hesaplanan bir sıraya göre ilk {num(data.top_n)} tür.
            Liste, <Term id="veri-boslugu">veri boşluğu</Term> analizinin eyleme dökülmüş hâlidir.
          </p>
        }
        how={
          <p>
            Her satırın puanı 0–1 arası bileşenlerden gelir; ağırlıklar yapılandırma dosyasındadır ve biyolog tarafından değiştirilebilir.
            “Neden bu tür?” sütunu, o sırayı hangi bileşenlerin taşıdığını düz Türkçe yazar. Ayrıntılı yöntem aşağıdadır.
          </p>
        }
      />

      <Callout tone="warn">
        <strong>Uyarı:</strong> Bu liste yalnızca açık veriden (WCVP yayılışı + ENA/INSDC barkod sayıları) üretilmiş bir öneridir.
        Tehdit durumu, örnek bulunabilirliği veya toplama zorluğu gibi alanlar boş bırakılmıştır; bunları uzman doldurmalıdır.
        IUCN veya kapalı kaynak kullanılmamıştır. Liste, uzman yargısının yerine geçmez.
      </Callout>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-sm font-semibold text-stone-600">Skorlanan boşluk türü</div>
          <div className="font-serif text-4xl font-bold text-link">{num(data.n_scored_gaps)}</div>
          <p className="mt-2 border-t border-stone-100 pt-2 text-sm text-stone-700">
            Boşluk kuralı: {markers} bölgelerinin hiçbirinde dizi yok
            {data.n_species_total ? <> (toplam {num(data.n_species_total)} tür içinden)</> : null}.
          </p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Listedeki endemik</div>
          <div className="font-serif text-4xl font-bold text-red-800">{num(endemicN)}</div>
          <p className="mt-2 border-t border-stone-100 pt-2 text-sm text-stone-700">
            İlk {num(data.top_n)} türün {num(endemicN)} tanesi ({pct(endemicN / data.top_n)}) WCVP’ye göre Türkiye endemiği.
          </p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Ne indirilir?</div>
          <p className="mt-2 text-sm text-stone-700">
            Tablodaki ilk {num(data.top_n)} türün CSV’si; tüm skorlanan türler için ayrıca depoda{" "}
            <code className="rounded bg-stone-100 px-1">exports/priority_all_scored.csv</code> vardır.
          </p>
        </Card>
      </div>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Puan nasıl hesaplanır?</h2>
        <p className="max-w-3xl text-stone-800">
          Yalnızca boşluk kuralına uyan türler puanlanır. Her bileşen 0–1 arasıdır; toplam, yapılandırmadaki ağırlıklarla çarpılıp toplanır
          (ağırlıklar toplamı 1’e normalize edilir). Varsayılan ağırlıklar yer tutucudur.
        </p>
        <ul className="max-w-3xl list-disc space-y-1 pl-5 text-stone-800">
          <li>
            <strong>Endemizm</strong> (ağırlık {pct(w.endemism)}): WCVP’ye göre yalnızca Türkiye’de doğal → 1, değilse 0.
          </li>
          <li>
            <strong>Dar yayılış</strong> (ağırlık {pct(w.range_restriction)}): 1 / (WCVP’deki doğal TDWG düzey-3 alan sayısı). Az alan = yüksek puan.
          </li>
          <li>
            <strong>Cins boşluğu</strong> (ağırlık {pct(w.genus_gap)}): Cinsteki türlerin kaçta kaçının aynı boşluk kuralına uyduğu; hiç verisi olmayan cinsler 1’e yaklaşır.
          </li>
          <li>
            <strong>Filogenetik yarar</strong> (ağırlık {pct(w.phylogenetic_usefulness)}): Aynı cinsten en az bir türde herhangi bir barkod dizisi varsa 1
            (yeni dizi mevcut ağaca / teste hemen eklenebilir), yoksa 0.
          </li>
          <li>
            <strong>Aile boşluğu</strong> (ağırlık {pct(w.family_gap)}): Ailedeki boşluk oranı (düşük kapsam = yüksek puan).
          </li>
        </ul>
        <p className="max-w-3xl text-stone-800">
          Boş bırakılan sütunlar (CSV’de): <em>threat_status_manual</em>, <em>specimen_availability</em>,{" "}
          <em>collection_difficulty</em>, <em>notes</em> — biyolog doldurur. Ağırlık duyarlılığı için{" "}
          <code className="rounded bg-stone-100 px-1">results/priority_sensitivity.csv</code> dosyasına bakın.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="mb-4 font-serif text-2xl font-bold text-stone-900">İlk {num(data.top_n)} tür</h2>
        <PriorityTable rows={data.species} />
      </section>

      <p className="mt-6 text-sm text-stone-600">
        İlgili sayfalar: <Link className="text-link underline" href="/veri-bosluklari">Veri boşlukları</Link>
        {" · "}
        <Link className="text-link underline" href="/yontem">Yöntem</Link>
        {" · "}
        <Link className="text-link underline" href="/sozluk">Sözlük</Link>
      </p>

      <Purpose>
        Sınırlı saha ve laboratuvar kaynağını, açık veriyle gerekçelendirilmiş bir sıraya göre kullanmak; hangi türün neden öne çıktığını herkesin görebilmesi.
      </Purpose>
    </div>
  );
}
