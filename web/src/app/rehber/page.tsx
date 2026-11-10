import type { Metadata } from "next";
import Link from "next/link";
import fs from "node:fs";
import path from "node:path";
import MarkerGuideTable, { type FamilyGuideRow } from "@/components/MarkerGuideTable";
import Term from "@/components/Term";
import { Callout, Card, PageIntro, PageTitle, Purpose } from "@/components/ui";
import { num } from "@/lib/format";

export const metadata: Metadata = { title: "Marker rehberi" };

type Payload = {
  criterion: string;
  pairing: string;
  min_shared_species: number;
  combinations: string;
  caveat: string;
  counts: {
    families: number;
    recommended: number;
    yetersiz_veri: number;
    fark_belirsiz: number;
  };
  families: FamilyGuideRow[];
};

function load(): Payload {
  const full = path.join(process.cwd(), "public", "data", "marker_guide.json");
  return JSON.parse(fs.readFileSync(full, "utf-8")) as Payload;
}

export default function MarkerGuidePage() {
  const data = load();
  const c = data.counts;

  return (
    <div>
      <PageTitle eyebrow="Marker rehberi" title="Hangi ailede hangi barkod bölgesi daha iyi ayırıyor?">
        Aynı türler üzerinde eşleştirilmiş karşılaştırma: ham başarı oranlarını farklı tür kümelerinde yan yana koymuyoruz.
      </PageTitle>
      <PageIntro
        what={
          <p>
            Her aile (ve büyük ailelerde cins) için, sitedeki <Term id="ayirt-edilebilirlik">katı tür düzeyi</Term> ölçüte göre
            hem A hem B bölgesinde değerlendirilmiş türlerde rbcL / matK / ITS karşılaştırması.
          </p>
        }
        how={
          <p>
            Önce öneri sütununa bakın. “Yetersiz veri” ortak tür &lt; {num(data.min_shared_species)} demektir.
            “Fark belirsiz” ortak küme yeterli ama Wilson %95 aralıkları örtüşüyor (veya eşleştirilmiş sınama net değil).
            Yeşil rozet, belirgin üstün çıkan bölgeyi gösterir. Altındaki cümle sayıları Türkçe biçimde yazar.
          </p>
        }
      />

      <Callout tone="warn">
        <strong>Uyarı:</strong> {data.caveat} Birleşik marker tanımı bu sürümde atlandı: {data.combinations}.
      </Callout>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-sm font-semibold text-stone-600">Öneri verilen aile</div>
          <div className="font-serif text-4xl font-bold text-link">{num(c.recommended)}</div>
          <p className="mt-2 text-sm text-stone-700">/ {num(c.families)} aile</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Yetersiz veri</div>
          <div className="font-serif text-4xl font-bold text-stone-700">{num(c.yetersiz_veri)}</div>
          <p className="mt-2 text-sm text-stone-700">Ortak tür eşiği: {num(data.min_shared_species)}</p>
        </Card>
        <Card>
          <div className="text-sm font-semibold text-stone-600">Fark belirsiz</div>
          <div className="font-serif text-4xl font-bold text-amber-800">{num(c.fark_belirsiz)}</div>
          <p className="mt-2 text-sm text-stone-700">Yeterli n, net üstünlük yok</p>
        </Card>
      </div>

      <section className="mt-10 space-y-3">
        <h2 className="font-serif text-2xl font-bold text-stone-900">Nasıl hesaplanır?</h2>
        <ul className="max-w-3xl list-disc space-y-1 pl-5 text-stone-800">
          <li>Ölçüt: {data.criterion}.</li>
          <li>Eşleştirme: {data.pairing}.</li>
          <li>Başarı oranına Wilson %95 güven aralığı; fark için aralık örtüşmesi veya McNemar (eşleştirilmiş) sınaması.</li>
          <li>Büyük ailelerde analiz cinslere bölünmüşse cins düzeyinde de aynı mantık uygulanır (CSV’de).</li>
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="mb-4 font-serif text-2xl font-bold text-stone-900">Aile tablosu</h2>
        <MarkerGuideTable rows={data.families} />
      </section>

      <p className="mt-6 text-sm text-stone-600">
        <Link className="text-link underline" href="/yontem">Yöntem</Link>
        {" · "}
        <Link className="text-link underline" href="/sozluk">Sözlük</Link>
        {" · "}
        <Link className="text-link underline" href="/">Ana sayfa</Link>
      </p>

      <Purpose>
        Hangi barkod bölgesinin hangi ailede daha ayırt edici göründüğünü, farklı tür kümelerini karıştırmadan göstermek.
      </Purpose>
    </div>
  );
}
