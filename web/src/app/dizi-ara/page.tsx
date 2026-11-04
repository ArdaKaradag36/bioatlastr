import type { Metadata } from "next";
import Link from "next/link";
import SequenceSearch from "@/components/SequenceSearch";
import Term from "@/components/Term";
import { Callout, PageIntro, PageTitle, Purpose } from "@/components/ui";
import { getMeta } from "@/lib/data.server";

export const metadata: Metadata = { title: "Dizi ara" };

export default function SequenceSearchPage() {
  const markers = Object.keys(getMeta().markers);
  return (
    <div>
      <PageTitle eyebrow="Dizi arama" title="Elinizdeki DNA dizisi hangi türe benziyor?">
        Bir DNA dizisini yapıştırın; sitedeki referans dizilerle karşılaştırılıp en çok benzeyen kayıtlar listelenir.
      </PageTitle>
      <PageIntro
        what={<p>Elinizde bir bitkiden okunmuş kısa bir DNA dizisi varsa, bu sayfa onu atlastaki <Term id="referans-dizi">referans dizilerle</Term> karşılaştırır ve en çok benzeyen kayıtları sıralar. Bu bir tür kimlik kontrolü değil, yalnızca bir ipucudur.</p>}
        how={
          <ol className="list-decimal space-y-1 pl-5">
            <li>Dizinizi aşağıdaki kutuya yapıştırın (düz harfler ya da <Term id="fasta">FASTA</Term> biçimi).</li>
            <li>Dizinin hangi <Term id="barkod-bolgesi">barkod bölgesine</Term> ait olduğunu seçin: {markers.join(", ")}.</li>
            <li>&quot;Karşılaştır&quot; düğmesine basın.</li>
            <li>Listede en üstteki türlerin <Term id="benzerlik">benzerlik yüzdesine</Term> bakın; her satırdan türün sayfasına gidebilirsiniz.</li>
          </ol>
        }
      />
      <div className="mb-6">
        <Callout>
          <strong>Gizlilik:</strong> Yapıştırdığınız dizi hiçbir yere gönderilmez ve saklanmaz. Karşılaştırma tamamen tarayıcınızda yapılır; yalnızca
          karşılaştırma için gereken referans dizi dosyaları siteden indirilir.
        </Callout>
        <p className="mt-3 max-w-3xl text-stone-700">
          <strong>Benzerlik yüzdesi ne demek?</strong> Sizin diziniz ile bir referans dizi hizalandığında, örtüşen bölgedeki harflerin ne kadarı aynıysa o kadar
          benzerlik vardır. <strong>Yüksek benzerlik, türün kesin olduğunu kanıtlamaz:</strong> aynı cinsten yakın türlerin dizileri de çok benzer olabilir,
          referans kayıt yanlış adlandırılmış olabilir ya da sizin türünüz atlasta hiç olmayabilir. Kesin tanı için uzman ve bitkinin kendisi gerekir.
        </p>
      </div>
      <SequenceSearch markers={markers} />
      <Purpose>
        DNA barkodlarının gerçek bir dizi karşısında nasıl çalıştığını denemek; hem yararını hem de sınırlarını kendi gözünüzle görmek. Terimler için <Link className="font-medium text-on-dark underline" href="/sozluk">Sözlük</Link>.
      </Purpose>
    </div>
  );
}
