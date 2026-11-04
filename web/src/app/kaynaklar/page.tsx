import type { Metadata } from "next";
import Term from "@/components/Term";
import { Card, PageIntro, PageTitle, Purpose, SectionTitle } from "@/components/ui";
import { getMeta, getTaxonNames } from "@/lib/data.server";
import { num } from "@/lib/format";
import CiteBox from "@/components/CiteBox";
import ContributeBox from "@/components/ContributeBox";
import { AUTHORS, CONTACT_EMAIL, PROJECT_TITLE, REPO_URL } from "@/lib/site";

export const metadata: Metadata = { title: "Kaynaklar ve lisanslar" };

const TIER: Record<string, string> = {
  A: "A — küratörlü, güvenilir, açık lisanslı kaynak",
};

function Cite({ children }: { children: React.ReactNode }) {
  return <p className="rounded-md bg-stone-100 p-3 text-sm text-stone-800">{children}</p>;
}

export default function SourcesPage() {
  const meta = getMeta();
  const tn = getTaxonNames().meta;
  const wcvp = meta.species_meta;
  const ena = meta.sequence_meta;
  return (
    <div className="max-w-4xl">
      <PageTitle title="Kaynaklar ve lisanslar">
        Sitedeki her verinin nereden geldiği, lisansı ve güvenilirlik düzeyi.
      </PageTitle>
      <PageIntro
        what={<p>Bu sitedeki tür listesinin, DNA dizilerinin ve Türkçe adların hangi kaynaklardan geldiğini, bu kaynakların lisanslarını ve nasıl anılması gerektiğini.</p>}
        how={<p>Her kaynağın yanında lisansı yazılıdır. Kısaltmalar (<Term id="wcvp">WCVP</Term>, <Term id="ena">ENA</Term>, <Term id="insdc">GenBank/INSDC</Term>) için Sözlük&apos;e bakabilirsiniz. Kaldırma ya da düzeltme isteği için sayfanın altındaki iletişim adresini kullanın.</p>}
      />

      <SectionTitle>Tür listesi ve diziler</SectionTitle>
      <ul className="list-disc space-y-2 pl-6 text-stone-800">
        <li>
          <strong>WCVP — World Checklist of Vascular Plants (Royal Botanic Gardens, Kew)</strong>: tür listesi, eş adlar, yayılış.
          Dosya tarihi {wcvp?.wcvp_file_date ?? "?"}. Lisans: CC BY 3.0 (Kew’in dağıttığı README_WCVP dosyasında belirtilmiştir). <a className="text-link underline" href="https://powo.science.kew.org/" target="_blank" rel="noreferrer">powo.science.kew.org</a>
        </li>
        <li>
          <strong>ENA — European Nucleotide Archive (EMBL-EBI, INSDC)</strong>: DNA dizileri; kayıtlar INSDC politikası gereği kullanım kısıtı olmadan sunulur; özgün gönderime erişim numarasıyla atıf yapılır.
          Alım tarihi {ena?.retrieved ?? "?"}. <a className="text-link underline" href="https://www.ebi.ac.uk/ena" target="_blank" rel="noreferrer">ebi.ac.uk/ena</a>
        </li>
      </ul>

      <SectionTitle>Türkçe adların kaynakları</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-600">
        Türkçe adlar elle yazılmamıştır; yalnızca aşağıdaki açık kaynaklardan alınmıştır ve bir uzman tarafından doğrulanmamıştır.
        Yalnızca serbestçe yeniden kullanılabilen (açık) lisanslı kaynaklar kullanılır; hepsi A düzeyindedir (küratörlü, güvenilir). Tablonun bütünü, Vikipedi (CC BY-SA) başlıkları içerdiği için CC BY-SA 4.0 altında sunulur.
      </p>
      <Card className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-stone-200 text-stone-500">
              <th className="p-2">Kaynak</th><th className="p-2">Düzey</th><th className="p-2">Lisans sınıfı</th><th className="p-2">Lisans</th><th className="p-2 text-right">Ad kaydı</th>
            </tr>
          </thead>
          <tbody>
            {tn?.sources_info.map((s) => (
              <tr key={s.label} className="border-b border-stone-100 align-top">
                <td className="p-2"><a className="text-link underline" href={s.url} target="_blank" rel="noreferrer">{s.label}</a></td>
                <td className="p-2" title={TIER[s.tier]}>{s.tier}</td>
                <td className="p-2">{s.license_class === "open" ? "açık" : "ticari olmayan"}</td>
                <td className="p-2 text-stone-600">{s.license}</td>
                <td className="p-2 text-right">{num(s.rows)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <ul className="mt-4 list-disc space-y-2 pl-6 text-stone-800">
        <li>
          <strong>Dışlananlar (C düzeyi):</strong> deniz türü kayıtları (WoRMS, WRiMS), DAISIE ve bir demiryolu projesinin çevresel etki
          değerlendirmesi veri seti sitede kullanılmaz ({num(tn?.excluded_rows ?? 0)} ad kaydı); lisansları ve uygunlukları belirsizdir.
        </li>
        <li>
          <strong>Kullanılmayan kaynaklar:</strong> iNaturalist ve IUCN Kırmızı Liste adları yalnızca ticari olmayan kullanıma izin verdiği için,
          GRIN Taxonomy (kendi sayfalarında veri lisansı doğrulanamadı) ile Türkiye Bitkileri Listesi / Bizim Bitkiler (NGBB) ise açık bir veri lisansı belirtmediği için bu sitede ve veri dosyalarında yer almaz.
        </li>
        <li>Tam liste: <code>data/names/LICENSES.md</code>; adların her satırında kaynak bağlantısı ve lisans vardır (<code>data/names/turkish_names.csv</code>).</li>
      </ul>

      <SectionTitle>Ekip</SectionTitle>
      <ul className="mb-8 list-disc space-y-1 pl-6 text-stone-800">
        {AUTHORS.map((a) => (
          <li key={a.family}>
            {a.given} {a.family} — {a.roleTr}
          </li>
        ))}
      </ul>

      <div id="atif" className="mb-6">
        <CiteBox />
      </div>
      <div id="katki" className="mb-8">
        <ContributeBox />
      </div>

      <SectionTitle>Atıf ve lisans</SectionTitle>
      <div className="max-w-3xl space-y-3 text-stone-800">
        <p>
          <strong>Bu sitenin kodu</strong> MIT lisanslıdır. <strong>Türetilmiş veri tabloları</strong> (kapsam, ayırt edilebilirlik sonuçları, dışa aktarımlar)
          kaynak veri sağlayıcılarına atıf yapılması koşuluyla CC BY 4.0 altında; <strong>Türkçe ad tablosu</strong> ve Türkçe ad içeren dışa aktarımlar CC BY-SA 4.0 altındadır.
          Ayrıntı: <code>DATA_LICENSE.md</code>, <code>THIRD_PARTY_NOTICES.md</code>.
        </p>
        <p className="font-medium">Gerekli atıflar ve önerilen kaynak gösterimi</p>
        <Cite>
          <strong>WCVP</strong> (CC BY 3.0): Govaerts R. (ed.) 2026. WCVP: World Checklist of Vascular Plants. Royal Botanic Gardens, Kew.
          https://doi.org/10.34885/egs6-cp24 [erişim 04 Haziran 2026]. Govaerts R., Nic Lughadha E. ve ark. (2021) The World Checklist of Vascular Plants, a continuously
          updated resource for exploring global plant diversity. Scientific Data 8: 215. https://doi.org/10.1038/s41597-021-00997-6
        </Cite>
        <Cite>
          <strong>ENA / INSDC</strong> (kullanım kısıtı yok; özgün gönderime atıf): dizilere erişim numarasıyla atıf yapın (ör. “GenBank/ENA MF596765”).
          Arşiv için: Burgin J. ve ark. (2023) The European Nucleotide Archive in 2022. Nucleic Acids Research 51: D121–D125. https://doi.org/10.1093/nar/gkac1051
        </Cite>
        <Cite>
          <strong>Wikidata</strong> (CC0 1.0): Wikidata contributors, https://www.wikidata.org, erişim 2026. &nbsp;
          <strong>Vikipedi</strong> (CC BY-SA 4.0): madde başlıkları, Vikipedi katkıcıları, https://tr.wikipedia.org (her ad satırında madde bağlantısı vardır; türetilmiş Türkçe ad tablosu da CC BY-SA 4.0’dır).
        </Cite>
        <Cite>
          <strong>Catalogue of Life</strong> (CC BY 4.0): Bánki O., Roskov Y., Döring M., Ower G. ve ark. (2026). Catalogue of Life (2026-08-26 XR). Catalogue of Life Foundation, Amsterdam.
          https://doi.org/10.48580/dgyy9 — GBIF aracılığıyla alınmıştır. &nbsp;
          <strong>Cichorieae Systematics Portal</strong> (CC BY 4.0): Kilian N. (2024) Botanic Garden and Botanical Museum Berlin. https://doi.org/10.15468/gzcrwf.
        </Cite>
        <Cite>
          <strong>Bu proje:</strong> {PROJECT_TITLE} (2026). {AUTHORS.map((a) => `${a.given} ${a.family}`).join(", ")}. Kod ve veri:{" "}
          <a className="text-link underline" href={REPO_URL}>{REPO_URL}</a>
        </Cite>
        <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900">
          <strong>Sorumluluk reddi:</strong> Bu site araştırma amaçlıdır; sonuçlar tahmin niteliğindedir, uzman doğrulaması yoktur ve
          bilimsel ya da ticari karar için kullanılmamalıdır. Türkçe adlar derlenmiş halk adlarıdır; bazıları birden fazla türe verilmiştir.
        </p>
        <p>
          <strong>Kaldırma ve iletişim:</strong> Bu sitede haklarınızı ihlal ettiğini düşündüğünüz bir içerik varsa ya da bir düzeltme istiyorsanız
          {" "}<a className="text-link underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>{" "}adresine yazın; içerik incelenir ve gerekirse gecikmeden kaldırılır.
        </p>
        <p>
          <strong>Gizlilik:</strong> Site çerez, analiz aracı ya da izleyici kullanmaz. Örnek toplayıcı adları, gönderen adları ve iletişim bilgileri yayımlanmaz.
        </p>
      </div>
      <Purpose>
        Verinin kaynağını ve lisansını açıkça belirtmek; bu çalışmanın kimlerin emeğine dayandığını göstermek ve kullanan herkesin doğru atıf yapabilmesini sağlamak.
      </Purpose>
    </div>
  );
}
