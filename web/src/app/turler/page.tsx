import type { Metadata } from "next";
import Link from "next/link";
import SpeciesBrowser from "@/components/SpeciesBrowser";
import { PageIntro, PageTitle, Purpose } from "@/components/ui";
import { getFamilies, getMeta, getStats } from "@/lib/data.server";
import { num } from "@/lib/format";

export const metadata: Metadata = { title: "Türler" };

export default function SpeciesListPage() {
  const families = getFamilies().map((f) => f.family);
  const markers = Object.keys(getMeta().markers);
  const total = getStats().totals.species;
  return (
    <div>
      <PageTitle eyebrow="Türler" title="Bitki türlerini keşfedin">
        Atlasta {num(total)} tür var. Latince ya da Türkçe adla arayın; ardından türün DNA barkodlarını, en yakın akrabalarını ve ağaçtaki konumunu görün.
      </PageTitle>
      <PageIntro
        what={<p>Türkiye florasındaki tüm türlerin listesi. Her satırda türün adı, ailesi ve üç barkod bölgesinden her biri için elimizdeki DNA dizisi sayısı yer alır.</p>}
        how={<p>Bir türün adına tıklayın; o türün sayfasında ne bildiğimizi ve neyin eksik olduğunu görürsünüz. Dizi sayısı 0 ise o bölge için kayıt yok demektir; bu bir <Link className="font-medium text-accent underline" href="/sozluk#veri-boslugu">veri boşluğudur</Link>. Latince adlar eğik yazılır.</p>}
      />
      <SpeciesBrowser families={families} markers={markers} />
      <Purpose>
        Her türün DNA barkodu durumunu tek tek görünür kılmak; hangi türlerin hazır verisi var, hangileri bekliyor bilinsin.
      </Purpose>
    </div>
  );
}
