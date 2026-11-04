import type { Metadata } from "next";
import Link from "next/link";
import { Card, PageTitle, SectionTitle } from "@/components/ui";
import { getMeta, getStats, getTaxonNames } from "@/lib/data.server";
import { DROP_REASONS, num, pct } from "@/lib/format";

export const metadata: Metadata = { title: "Yöntem ve sınırlılıklar" };

function stepLabel(step: string): string {
  if (step === "raw_records") return "ENA'dan gelen ham kayıt (marker sınıflandırması sonrası)";
  if (step === "name_matched") return "Türkiye florası adıyla eşleşen kayıt";
  if (step === "kept") return "Tutulan dizi (nihai)";
  if (step === "kept_from_turkey") return "…bunlardan Türkiye örneği";
  const reason = step.replace("dropped:", "");
  return `Atılan: ${DROP_REASONS[reason] ?? reason}`;
}

export default function MethodPage() {
  const meta = getMeta();
  const stats = getStats();
  const tn = getTaxonNames().meta;
  const markers = Object.keys(meta.markers);
  const sp = meta.species_meta;
  const sq = meta.sequence_meta;
  const generated = new Date(meta.generated_at).toLocaleString("tr-TR");
  const summaryMarkers = [...new Set(stats.filter_summary.map((r) => r.marker))].filter((m) => markers.includes(m));
  const steps = [...new Set(stats.filter_summary.map((r) => r.step))].sort((a, b) => {
    const order = (s: string) => (s === "raw_records" ? 0 : s.startsWith("dropped") ? 1 : s === "name_matched" ? 2 : s === "kept" ? 3 : 4);
    return order(a) - order(b) || a.localeCompare(b);
  });
  const cell = (m: string, step: string) => stats.filter_summary.find((r) => r.marker === m && r.step === step)?.count;

  return (
    <div className="prose-custom max-w-3xl">
      <PageTitle title="Yöntem ve sınırlılıklar">
        Rakamların nereden geldiği, hangi filtrelerin uygulandığı ve sonuçlara ne kadar güvenilebileceği.
      </PageTitle>

      {meta.max_species !== null || meta.families.length > 0 ? (
        <div className="mb-6 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          <strong>Not:</strong> Bu sürüm Türkiye florasının <em>tamamını</em> kapsamayan kısmi bir çalıştırmadır
          {meta.families.length > 0 && <> (aileler: {meta.families.join(", ")})</>}
          {meta.max_species !== null && <> (en çok {num(meta.max_species)} tür)</>}. Tam veri hazır olduğunda site yeniden
          derlenir.
        </div>
      ) : null}

      <Card>
        <h2 className="mb-2 text-lg font-semibold text-stone-800">Sonuçları okurken bilinmesi gerekenler</h2>
        <ul className="list-disc space-y-2 pl-5 text-stone-700">
          <li>
            <strong>Başarı yalnızca en az 2 dizisi olan türlerde ölçülür:</strong>{" "}
            {markers.map((m, i) => (
              <span key={m}>
                {i > 0 && "; "}
                {m}: {num(stats.markers[m].discrimination.species_evaluated)} tür
              </span>
            ))}{" "}
            ({num(stats.totals.species)} türün çoğunda bu koşul sağlanmaz). Tek dizisi olan türler başarı oranına girmez.
          </li>
          <li>
            <strong>Büyük aileler cinslere bölündü:</strong> bir markerde {num(meta.max_group_sequences)} diziden fazlası olan
            aileler (ör. Asteraceae, Fabaceae, Poaceae) cins cins analiz edildi; cins içi karşılaştırma ailenin tamamına göre
            daha kolaydır, başarı olduğundan iyimser olabilir.
          </li>
          <li>
            <strong>Diziler yalnızca {pct(stats.totals.sequences_from_turkey / stats.totals.sequences)}
            oranında Türkiye örneğidir</strong> ({num(stats.totals.sequences_from_turkey)} / {num(stats.totals.sequences)}); çoğu dizi
            başka ülkelerdeki örneklerden gelir. Türkiye popülasyonlarının varyasyonu tam yansımayabilir.
          </li>
          <li>
            <strong>Sürümler:</strong> tür listesi WCVP dosya tarihi {sp?.wcvp_file_date ?? "?"} (indirme {sp?.downloaded ?? "?"});
            diziler ENA&apos;dan {sq?.retrieved ?? "?"} tarihinde alındı.
          </li>
          <li>
            <strong>Yöntem:</strong> p-mesafesine dayalı en yakın komşu (best close match); hizalama{" "}
            <strong>{meta.aligner_label}</strong> ile yapıldı.
          </li>
        </ul>
      </Card>

      <SectionTitle>1. Veri kaynakları</SectionTitle>
      <ul className="list-disc space-y-2 pl-6 text-stone-700">
        <li>
          <strong>Tür listesi — WCVP</strong> (World Checklist of Vascular Plants, Royal Botanic Gardens, Kew).{" "}
          {sp ? (
            <>
              Dosya tarihi: <strong>{sp.wcvp_file_date ?? "?"}</strong>, indirme tarihi: <strong>{sp.downloaded}</strong>.
              Kural: {sp.rules}. Bu çalıştırmada {num(sp.species_in_file)} tür ({num(sp.endemic_in_file)} endemik) ve{" "}
              {num(sp.synonyms_in_file)} eş ad (synonym) kullanıldı.
            </>
          ) : (
            "Sürüm bilgisi bulunamadı."
          )}
        </li>
        <li>
          <strong>Diziler — ENA</strong> (European Nucleotide Archive; GenBank/DDBJ ile eşlenen INSDC aynası).{" "}
          {sq ? (
            <>
              Veri alma tarihi: <strong>{sq.retrieved}</strong>. {num(sq.genera_queried)} cins sorgulandı
              (cins → ENA takson numarası; <code>tax_tree</code> sorgusu), {num(sq.genera_unresolved.length)} cins ENA
              taksonomisinde bulunamadı (çoğu eş ad olan cins adlarıdır; kabul edilmiş cinslerden{" "}
              {num(sq.accepted_genera_without_ena_taxon?.length ?? 0)} tanesi bulunamadı).
            </>
          ) : (
            "Veri alma tarihi bulunamadı."
          )}{" "}
          Sorgular tür değil <em>cins</em> bazlıdır; kayıt adı tür listesiyle eşleştirilir. Hiçbir hesap ya da anahtar
          kullanılmaz.
        </li>
      </ul>

      <SectionTitle>2. Ad eşleştirme</SectionTitle>
      <ul className="list-disc space-y-2 pl-6 text-stone-700">
        <li>
          Kayıttaki bilimsel ad (alt türler/varyeteler cins + tür adına indirgenir) önce WCVP kabul edilmiş adıyla,
          sonra WCVP eş adlarıyla eşleştirilir; eş ad tek bir kabul edilmiş Türkiye türüne gidiyorsa kullanılır, birden
          fazlasına gidiyorsa <em>belirsiz</em> sayılıp atılır.
        </li>
        <li>
          Eşleşmeyen adlar atılır ve <code>data/unmatched_names.csv</code> dosyasına yazılır
          ({num(stats.unmatched_names_total)} farklı ad).
        </li>
        <li>
          <em>sp.</em>, <em>cf.</em>, <em>aff.</em>, melez (×) ve <code>UNVERIFIED</code> kayıtları ile &quot;Cins tür&quot;
          biçiminde olmayan adlar atılır.
        </li>
      </ul>

      <SectionTitle>3. Kalite filtreleri</SectionTitle>
      <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-left text-stone-600">
            <tr>
              <th className="p-3">Marker</th>
              <th className="p-3 text-right">En az uzunluk (bp)</th>
              <th className="p-3 text-right">En çok uzunluk (bp)</th>
              <th className="p-3 text-right">En çok N oranı</th>
            </tr>
          </thead>
          <tbody>
            {markers.map((m) => (
              <tr key={m} className="border-t border-stone-100">
                <td className="p-3 font-medium">{m}</td>
                <td className="p-3 text-right">{num(meta.markers[m].min_length)}</td>
                <td className="p-3 text-right">{num(meta.markers[m].max_length)}</td>
                <td className="p-3 text-right">%{(meta.markers[m].max_n_fraction * 100).toLocaleString("tr-TR")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="mt-4 list-disc space-y-2 pl-6 text-stone-700">
        <li>Aralık bölgeleri (ör. atpB-rbcL), tüm genom/plastom kayıtları ve sözde genler atılır; çok uzun kayıtlar elenir.</li>
        <li>Birden fazla markeri aynı kayıtta taşıyan kayıtlar atılır.</li>
        <li>
          Aynı dizinin en çok {num(meta.max_identical_copies)} kopyası tutulur (yakın tekrar sınırı); tür ve marker başına en
          çok {num(meta.max_sequences_per_species_marker)} dizi tutulur, Türkiye örnekleri öncelikli, sonra farklı ve uzun diziler.
        </li>
      </ul>

      {summaryMarkers.length > 0 && (
        <>
          <h3 className="mb-2 mt-6 text-lg font-semibold">Kayıt sayıları: ham / atılan / tutulan</h3>
          <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-left text-stone-600">
                <tr>
                  <th className="p-3">Adım</th>
                  {summaryMarkers.map((m) => <th key={m} className="p-3 text-right">{m}</th>)}
                </tr>
              </thead>
              <tbody>
                {steps.map((s) => (
                  <tr key={s} className="border-t border-stone-100">
                    <td className="p-3">{stepLabel(s)}</td>
                    {summaryMarkers.map((m) => (
                      <td key={m} className="p-3 text-right font-mono text-xs">{num(cell(m, s) ?? 0)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tn && (
        <>
          <SectionTitle>Türkçe adlar</SectionTitle>
          <ul className="list-disc space-y-2 pl-6 text-stone-700">
            <li>
              Türkçe adlar <strong>elle yazılmamıştır</strong>; yalnızca açık kaynaklardan alınmıştır:{" "}
              {tn.sources.join(", ")}. Her ad, geldiği kaynağa bağlantıyla birlikte tür sayfasında gösterilir. Latince adla aynı olan
              kayıtlar atılmıştır; eş adlara (synonym) bağlı adlar kabul edilmiş türe aktarılmıştır.
            </li>
            <li>
              Kaynaklar güvenilirlik düzeyine (A: küratörlü, B: topluluk katkılı / kısıtlı lisanslı) ve lisans sınıfına (açık /
              ticari olmayan) ayrılmıştır; deniz türü kayıtları gibi uygun olmayan kaynaklar (C düzeyi) dışlanmıştır. Her adın yanında
              kaynağı, düzeyi ve lisansı gösterilir; tam liste <Link className="underline" href="/kaynaklar">Kaynaklar ve lisanslar</Link> sayfasındadır.
            </li>
            <li>
              <strong>Kapsam kısmidir:</strong> {num(tn.species_total)} türün {num(tn.species_with_name)} tanesi
              ({pct(tn.species_with_name / tn.species_total)}), cinslerden {num(tn.genus_with_name)}, ailelerden {num(tn.family_with_name)}
              tanesi en az bir Türkçe ada sahiptir.
            </li>
            <li>
              <strong>Adlar bir uzman tarafından doğrulanmamıştır</strong> (kaynaklar arası tutarsızlık, Latince harfsiz yazımlar ve
              hatalı eşleşmeler olabilir). Biyolog doğrulaması için <code>exports/</code> klasöründeki şablon kullanılır.
            </li>
            <li>
              <strong>Ortak adlar belirsiz olabilir:</strong> aynı Türkçe ad (ör. &quot;kekik&quot;) birden çok türe verilebilir;
              {" "}{num(tn.ambiguous_species_names)} Türkçe ad birden fazla türde kullanıldığı için &quot;birden çok türde kullanılan ad&quot;
              olarak işaretlenmiştir.
            </li>
            <li>
              Türkiye Bitkileri Listesi (Bizim Bitkiler, NGBB) gibi kapsamlı Türkçe ad kaynaklarının kullanım koşulları açık bir veri
              lisansı belirtmediği için bu kaynak <em>kullanılmamıştır</em>.
            </li>
          </ul>
        </>
      )}

      <SectionTitle>4. Hizalama, mesafe ve ağaç</SectionTitle>
      <ul className="list-disc space-y-2 pl-6 text-stone-700">
        <li>
          Hizalama yöntemi: <strong>{meta.aligner_label}</strong>
          {meta.aligner === "mafft" ? " (MAFFT --auto, ters yönlü diziler otomatik düzeltilir)." : " — MAFFT bulunamadığı için Biopython tabanlı yedek yöntem; tüm sonuçlar ön sonuçtur."}
        </li>
        <li>
          Her <em>aile</em> ve marker için ayrı hizalama yapılır; bir ailenin bir markerde {num(meta.max_group_sequences)}
          diziden fazlası varsa aile <em>cins cins</em> analiz edilir. Bir grupta {num(meta.min_group_sequences)}&apos;ten az
          dizi ya da tek tür varsa grup atlanır ve kaydedilir ({num(stats.groups_skipped)} grup atlandı,{" "}
          {num(stats.groups_analysed)} grup analiz edildi).
        </li>
        <li>
          Mesafe: <strong>p-mesafesi</strong> (farklı baz / karşılaştırılabilir baz; boşluk ve belirsiz bazlar yok sayılır, en
          az {num(meta.min_overlap)} ortak baz gerekir). Ağaçlar komşu birleştirme (NJ) ile kurulur ve orta noktadan köklendirilir.
        </li>
      </ul>

      <SectionTitle>5. Ayırt etme başarısı nasıl ölçülür?</SectionTitle>
      <p className="text-stone-700">
        <strong>&quot;En yakın eşleşme&quot; (best close match)</strong>: en az 2 dizisi olan türlerin her dizisi için, kendisi
        dışındaki tüm dizilerle p-mesafesine bakılır. <strong>Başarılı:</strong> en yakın komşu aynı tür;{" "}
        <strong>belirsiz:</strong> eşitlik; <strong>başarısız:</strong> en yakın komşu başka tür.
      </p>
      <p className="mt-3 text-stone-700">
        <strong>Marker kombinasyonları</strong> tür düzeyinde değerlendirilir: türün kendi içindeki en küçük mesafesi,
        başka bir türe olan en küçük mesafeden küçükse başarılıdır; kombinasyon mesafesi, iki türün birlikte verisi olan
        markerların mesafe ortalamasıdır. Mesafesi 0 olan tür çiftleri ve her türün en yakın {num(meta.n_nearest)} akrabası
        ayrıca verilir.
      </p>

      <SectionTitle>6. Bilinen riskler ve sınırlılıklar</SectionTitle>
      <Card>
        <ul className="list-disc space-y-3 pl-5 text-stone-700">
          <li>
            <strong>Hatalı tanımlanmış kayıtlar.</strong> INSDC kayıtlarının tür adı yükleyen kişiye güvenilerek kabul
            edilir; doğrulanmaz. Yanlış adlandırılmış diziler başarıyı düşürebilir ya da olduğundan iyi gösterebilir.
          </li>
          <li>
            <strong>Eksik türler.</strong> Dizisi olmayan türler veri boşluğudur (bkz.{" "}
            <Link className="underline" href="/veri-bosluklari">Veri boşlukları</Link>). Kayıtta farklı bir ad
            (WCVP&apos;de olmayan eş ad) kullanıldıysa tür eksik görünebilir.
          </li>
          <li>
            <strong>Grup içi karşılaştırma.</strong> Diziler yalnızca aynı aile (büyük ailelerde aynı cins) içindeki
            dizilerle kıyaslanır; bu, başarıyı iyimser gösterebilir.
          </li>
          <li>
            <strong>Örneklem küçüklüğü.</strong> Bir türün 1–2 dizisi tüm çeşitliliği temsil etmez.
          </li>
          <li>
            <strong>Basit model.</strong> p-mesafesi ve NJ hızlı yöntemlerdir; ağaç kesin akrabalık kanıtı değildir.
          </li>
          <li>
            <strong>Tür listesi.</strong> WCVP&apos;nin &quot;Türkiye&apos;de doğal, soyu tükenmemiş, şüpheli olmayan&quot; kabul
            edilmiş türleri alınır; melezler dışarıda bırakılır. Taksonomik görüşler değişebilir.
          </li>
          <li>
            <strong>Dizi arama</strong> sayfası tarayıcıda çalışan basit bir k-mer + ikili hizalama yöntemidir; sonuçlar
            gösterge niteliğindedir, BLAST&apos;ın ve uzman doğrulamasının yerini tutmaz.
          </li>
        </ul>
      </Card>

      <SectionTitle>7. Verinin üretimi</SectionTitle>
      <p className="text-stone-700">
        Veri <strong>{generated}</strong> tarihinde, boru hattı sürümü {meta.pipeline_version} ile üretilmiştir. Komutlar{" "}
        <code>README.md</code>, CSV özetleri <code>results/</code> klasöründedir.
      </p>
    </div>
  );
}
