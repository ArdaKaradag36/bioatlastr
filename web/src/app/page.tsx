import Link from "next/link";
import { BookIcon, DnaIcon, GapIcon, HeroArt, LeafIcon, ListIcon, SearchIcon, ShieldIcon, TargetIcon, TreeIcon } from "@/components/Icons";
import SpeciesSearch from "@/components/SpeciesSearch";
import Term from "@/components/Term";
import { Bar, Card, COVERAGE_COLORS, Legend, PageIntro, Purpose, SectionTitle, StackedBar, StatCard } from "@/components/ui";
import { getFamilies, getMeta, getStats } from "@/lib/data.server";
import { num, pct } from "@/lib/format";
import { per100, sequenceRateSentence, speciesRateSentence } from "@/lib/plain";

const MARKER_TERM: Record<string, string> = { rbcL: "rbcl", matK: "matk", ITS: "its" };

export default function HomePage() {
  const stats = getStats();
  const meta = getMeta();
  const families = getFamilies();
  const markers = Object.keys(meta.markers);
  const t = stats.totals;
  const comboRows = stats.combinations.filter((c) => c.n_markers > 1);
  const bestStrict = markers
    .map((m) => ({ m, d: stats.markers[m].discrimination }))
    .filter((x) => x.d.species_success_rate != null)
    .sort((a, b) => (b.d.species_success_rate ?? 0) - (a.d.species_success_rate ?? 0))[0];
  const markerList = markers.map((m, i) => (
    <span key={m}>
      {i > 0 && (i === markers.length - 1 ? " ve " : ", ")}
      {MARKER_TERM[m] ? <Term id={MARKER_TERM[m]}>{m}</Term> : m}
    </span>
  ));

  return (
    <div>
      {/* ---------------- Hero */}
      <section className="rise relative overflow-hidden rounded-3xl bg-gradient-to-br from-forest to-forest-2 px-6 py-10 text-on-dark sm:px-12 sm:py-14">
        <div className="grid items-center gap-8 md:grid-cols-[1.25fr_1fr]">
          <div>
            <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-leaf">Üniversite öğrenci araştırma projesi</p>
            <h1 className="font-serif text-3xl font-bold leading-tight text-on-dark sm:text-5xl">
              Bir bitkiyi, DNA&apos;sının kısa bir bölümünden tanıyabilir miyiz?
            </h1>
            <p className="mt-4 max-w-xl text-lg leading-relaxed text-snow/90">
              Bu atlas, Türkiye&apos;de yetişen bitki türlerinin kısa <Term id="dna-barkodu">DNA barkodlarıyla</Term> ({markerList}) birbirinden ayırt
              edilip edilemediğini araştırır. Hangi türlerin barkodunun kayıtlı, hangilerinin hâlâ eksik olduğunu da herkesin
              okuyabileceği bir dille gösterir.
            </p>
            <div className="mt-6 max-w-xl text-stone-900">
              <SpeciesSearch placeholder="Tür ara: meşe, kızılçam, Quercus…" autoFocus={false} />
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/turler" className="inline-flex min-h-12 items-center rounded-xl bg-snow px-5 font-semibold text-forest hover:bg-snow/90">Türlere göz at</Link>
              <Link href="/sozluk" className="inline-flex min-h-12 items-center rounded-xl border border-snow/50 px-5 font-semibold text-on-dark hover:bg-snow/10">Sözlük: terimler ne demek?</Link>
            </div>
          </div>
          <div className="hidden md:block"><HeroArt /></div>
        </div>
      </section>

      <div className="mt-8">
        <PageIntro
          what={
            <p>
              Türkiye&apos;nin bitki türlerinin kaçında DNA barkodu bulunduğunu ve bu kısa DNA bölümlerinin türleri birbirinden ne kadar ayırabildiğini
              gösteren bir özet. Aşağıdaki her kutunun altında sayının ne anlama geldiğini bir cümleyle de yazıyoruz.
            </p>
          }
          how={
            <p>
              Önce &quot;Nasıl çalışır?&quot; bölümüne bakın, sonra rakamlara geçin. Altı çizili (noktalı) sözcüklerin üzerine gelin ya da dokunun:
              küçük bir açıklama çıkar. Hepsi <Link className="font-medium text-accent underline" href="/sozluk">Sözlük</Link> sayfasında da var.
            </p>
          }
        />
      </div>

      {/* ---------------- First visit */}
      <section aria-labelledby="ilk-kez" className="rise-3">
        <h2 id="ilk-kez" className="mb-4 text-2xl font-semibold sm:text-3xl">İlk kez mi geldiniz? Üç adımda tanışın</h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {[
            { n: 1, href: "/turler", icon: <SearchIcon />, title: "Bir tür ara", text: "Latince ya da Türkçe adını yazın; o türün DNA barkodlarını ve en yakın akrabalarını görün." },
            { n: 2, href: "/agaclar", icon: <TreeIcon />, title: "Ağaca bak", text: "Bir aile seçin; dizilerin benzerliğine göre çizilmiş akrabalık ağacında türünüzü bulun." },
            { n: 3, href: "/sozluk", icon: <BookIcon />, title: "Sözlüğe göz at", text: "Merak ettiğiniz her terimin sade Türkçe açıklaması burada: rbcL nedir, p-mesafesi nedir?" },
          ].map((s) => (
            <li key={s.n}>
              <Link href={s.href} className="lift group flex h-full gap-4 rounded-2xl border border-stone-200 bg-white p-5 shadow-card hover:border-emerald-400">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-emerald-100 font-serif text-xl font-bold text-link">{s.n}</span>
                <span>
                  <span className="flex items-center gap-2 font-serif text-lg font-semibold text-stone-900 group-hover:text-link">{s.icon}{s.title}</span>
                  <span className="mt-1 block text-stone-700">{s.text}</span>
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      {/* ---------------- How it works */}
      <SectionTitle id="nasil-calisir">Nasıl çalışır?</SectionTitle>
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: <ListIcon width={34} height={34} />, title: "1. Tür listesi", text: <>Kew&apos;in <Term id="wcvp">WCVP</Term> listesinden, Türkiye&apos;de doğal olarak yetişen kabul edilmiş türleri aldık.</>, href: "/yontem#kaynaklar" },
          { icon: <DnaIcon width={34} height={34} />, title: "2. DNA dizileri", text: <>Bilim insanlarının <Term id="ena">ENA</Term> arşivine yüklediği barkod <Term id="dizi">dizilerini</Term> indirdik ve kalite denetiminden geçirdik.</>, href: "/yontem#filtreler" },
          { icon: <TreeIcon width={34} height={34} />, title: "3. Akrabalık ağacı", text: <>Dizileri <Term id="hizalama">hizaladık</Term>, aralarındaki farkı ölçtük ve benzerliklerine göre bir <Term id="filogenetik-agac">ağaç</Term> çizdik.</>, href: "/agaclar" },
          { icon: <TargetIcon width={34} height={34} />, title: "4. Sonuç", text: <>Her dizinin en yakın komşusunun aynı türden olup olmadığına baktık; böylece barkodun türü <Term id="ayirt-edilebilirlik">ayırt etme</Term> gücünü ölçtük.</>, href: "/yontem#olcum" },
        ].map((s) => (
          <li key={s.title}>
            <Link href={s.href} className="lift flex h-full flex-col rounded-2xl border border-stone-200 bg-white p-5 shadow-card hover:border-emerald-400">
              <span className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-link">{s.icon}</span>
              <span className="font-serif text-lg font-semibold text-stone-900">{s.title}</span>
              <span className="mt-1 flex-1 text-stone-700">{s.text}</span>
              <span className="mt-3 text-sm font-medium text-link">Ayrıntılar →</span>
            </Link>
          </li>
        ))}
      </ol>

      {/* ---------------- Headline numbers */}
      <SectionTitle id="rakamlar">Rakamlarla atlas</SectionTitle>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Türkiye florasındaki tür sayısı"
          value={num(t.species)}
          note={`${num(t.families)} aile, ${num(t.genera)} cins`}
          meaning={<>Bunların {num(t.endemic_species)} tanesi ({pct(t.endemic_species / t.species)}) WCVP&apos;ye göre yalnızca Türkiye&apos;de yetişen <Term id="endemik">endemik</Term> türdür. Bu bir Kırmızı Liste (IUCN) değerlendirmesi değildir.</>}
        />
        <StatCard
          label="DNA barkodu olan tür"
          value={num(t.species_with_any_sequence)}
          note={pct(t.species_with_any_sequence / t.species)}
          meaning={<>Her 100 türden yaklaşık {per100(t.species_with_any_sequence / t.species)} tanesinin, üç bölgeden en az birinde kayıtlı dizisi var.</>}
        />
        <StatCard
          label="Kullandığımız DNA dizisi"
          value={num(t.sequences)}
          note="kalite denetiminden geçen kayıt"
          meaning={<>Bunların {num(t.sequences_from_turkey)} tanesi ({pct(t.sequences_from_turkey / t.sequences)}) Türkiye&apos;den toplanan örneklere ait; gerisi başka ülkelerden.</>}
        />
        <StatCard
          label="DNA barkodu eksik tür"
          value={num(t.species_without_sequences)}
          note={pct(t.species_without_sequences / t.species)}
          meaning={<>ENA/INSDC&apos;de kayıt bulunamadı. BOLD taranmadı; gelecek çalışma olarak planlandı. Bunların {num(t.endemic_without_sequence)} tanesi endemik. <Link className="font-medium text-link underline" href="/veri-bosluklari">Hangileri?</Link></>}
        />
      </div>

      {/* ---------------- Per marker */}
      <SectionTitle id="bolgeler">Hangi barkod bölgesi türleri ne kadar ayırıyor?</SectionTitle>
      <p className="mb-4 max-w-3xl text-stone-700">
        Üç <Term id="barkod-bolgesi">barkod bölgesini</Term> ayrı ayrı sınadık. Resmî başarı tanımı <strong>katıdır</strong>: bir türün değerlendirilen
        bütün dizilerinin <Term id="en-yakin-komsu">en yakın komşusu</Term> aynı tür olmalıdır. Karşılaştırma aynı aile içindedir (çok büyük ailelerde aynı cins);
        bu, başarıyı biraz iyimser gösterebilir. Yalnızca birden çok dizisi olan türler sınanabilir. Hizalama: <strong>{meta.aligner_label}</strong>.
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        {markers.map((m) => {
          const s = stats.markers[m];
          const d = s.discrimination;
          return (
            <Card key={m} className="flex flex-col">
              <div className="flex items-baseline justify-between">
                <h3 className="font-serif text-2xl font-semibold">{MARKER_TERM[m] ? <Term id={MARKER_TERM[m]}>{m}</Term> : m}</h3>
                <span className="text-sm text-stone-600">{num(s.sequences)} dizi</span>
              </div>
              <div className="mt-3 font-serif text-5xl font-bold text-link">{pct(d.species_success_rate)}</div>
              <p className="mt-1 text-sm font-medium text-stone-700">türlerde ayırt etme başarısı</p>
              <p className="mt-2 text-stone-800">{speciesRateSentence(d.species_success_rate, d.species_evaluated)} Karşılaştırma aile/cins içidir.</p>
              <p className="mt-2 text-sm text-stone-600">{sequenceRateSentence(d.success_rate, d.sequences_evaluated)}</p>
              {m === "ITS" && (
                <p className="mt-2 rounded-lg bg-amber-50 p-2 text-sm text-amber-900">
                  ITS nükleer, çok kopyalı bir bölgedir; paralog kopyalar ve mantar bulaşması sonucu bozabilir. Aşağıdaki &quot;en yüksek
                  katı başarı&quot; cümlesi de bu bölgeye aitse bu uyarı geçerlidir ({num(d.species_evaluated)} tür).
                </p>
              )}
              <div className="mt-4">
                <div className="mb-1 text-sm font-medium text-stone-700">Kaç türün bu bölgede dizisi var?</div>
                <StackedBar
                  segments={[
                    { label: "Dizi yok", value: s.species_0, color: COVERAGE_COLORS.zero },
                    { label: "1 dizi", value: s.species_1, color: COVERAGE_COLORS.one },
                    { label: "2 ve üzeri dizi", value: s.species_2plus, color: COVERAGE_COLORS.twoPlus },
                  ]}
                />
                <p className="mt-2 text-sm text-stone-600">
                  {num(s.species_0)} türün hiç dizisi yok · {num(s.species_1)} türün tek dizisi var · {num(s.species_2plus)} türün iki ya da daha çok dizisi var.
                </p>
              </div>
              <p className="mt-3 text-sm text-stone-600">
                Bu bölgede dizileri tamamen aynı (mesafe 0) çıkan <Term id="belirsiz-cift">tür çifti</Term> sayısı: {num(s.zero_distance_pairs)}.
              </p>
            </Card>
          );
        })}
      </div>
      <div className="mt-3">
        <Legend
          items={[
            { label: "Dizi yok", color: COVERAGE_COLORS.zero },
            { label: "1 dizi", color: COVERAGE_COLORS.one },
            { label: "2 ve üzeri dizi", color: COVERAGE_COLORS.twoPlus },
          ]}
        />
      </div>

      {/* ---------------- Combinations */}
      <SectionTitle id="kombinasyonlar">Bölgeleri birlikte kullanırsak?</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700">
        {bestStrict && (
          <>
            Resmî (katı) tanıma göre tek bölgeler arasında en yüksek tür başarısı <strong>{bestStrict.m}</strong> içindir:
            değerlendirilen her 100 türden yaklaşık {per100(bestStrict.d.species_success_rate)} tanesi ayırt edildi
            ({num(bestStrict.d.species_evaluated)} tür üzerinden).
            {bestStrict.m === "ITS" && (
              <> ITS nükleer ve çok kopyalıdır; bu yüzde paralog veya mantar bulaşması nedeniyle şişmiş olabilir.</>
            )}
            {" "}
          </>
        )}
        Aşağıdaki tablo <strong>farklı, daha gevşek bir tanımdır</strong>: bir tür, kendi dizileri arasındaki en küçük fark başka bir türe
        olan en küçük farktan küçükse &quot;ayırt edildi&quot; sayılır (bölge mesafelerinin ortalaması). Dizilerin tümünün geçmesi gerekmez.
        Yalnızca ilgili bölgelerin hepsinde değerlendirilebilen türler tabloya girer.
      </p>
      <div tabIndex={0} className="overflow-x-auto rounded-2xl border border-stone-200 bg-white shadow-card">
        <table className="w-full text-[0.95rem]">
          <caption className="sr-only">Barkod bölgesi kombinasyonlarına göre tür düzeyinde ayırt etme sonuçları</caption>
          <thead className="bg-stone-50 text-left text-stone-700">
            <tr>
              <th scope="col" className="p-3">Bölge / kombinasyon</th>
              <th scope="col" className="p-3 text-right">Değerlendirilen tür</th>
              <th scope="col" className="p-3 text-right">Ayırt edilen</th>
              <th scope="col" className="p-3 text-right">Belirsiz</th>
              <th scope="col" className="p-3 text-right">Ayırt edilemeyen</th>
              <th scope="col" className="p-3 text-right">Başarı oranı</th>
            </tr>
          </thead>
          <tbody>
            {comboRows.map((c) => (
              <tr key={c.combination} className="border-t border-stone-100">
                <th scope="row" className="p-3 text-left font-medium">{c.combination.replaceAll("+", " + ")}</th>
                <td className="p-3 text-right">{num(c.species_evaluated)}</td>
                <td className="p-3 text-right">{num(c.success)}</td>
                <td className="p-3 text-right">{num(c.ambiguous)}</td>
                <td className="p-3 text-right">{num(c.fail)}</td>
                <td className="p-3 text-right font-semibold text-link">{pct(c.success_rate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-sm text-stone-600">
        &quot;Belirsiz&quot;: en küçük fark hem kendi türüne hem başka bir türe aynı çıktı. Başarı oranı = ayırt edilen / değerlendirilen tür.
      </p>

      {/* ---------------- Families */}
      <SectionTitle id="aileler">Hangi ailelerde barkod verisi var?</SectionTitle>
      <p className="mb-3 max-w-3xl text-stone-700">
        En çok türü olan 25 <Term id="familya">aile</Term> aşağıda. Her çubuk, ailedeki türlerin kaçında en az bir DNA barkodu olduğunu gösterir; çubuğa ya da aile adına tıklayarak
        ailenin ağacına gidebilirsiniz.
      </p>
      <Card>
        <ul className="space-y-3">
          {[...families].sort((a, b) => b.species - a.species).slice(0, 25).map((f) => {
            const fs = stats.families[f.family];
            return (
              <li key={f.family} className="grid items-center gap-1 sm:grid-cols-[10rem_1fr_11rem] sm:gap-3">
                <Link href={`/agaclar?aile=${f.family}`} className="py-1 font-medium text-link hover:underline">
                  {f.family}
                </Link>
                <Bar value={fs.species_with_any_sequence} max={fs.species} label={`${f.family}: ${num(fs.species)} türün ${num(fs.species_with_any_sequence)} tanesinde dizi var`} />
                <span className="text-sm text-stone-700 sm:text-right">
                  {num(fs.species)} türün {num(fs.species_with_any_sequence)} tanesinde dizi var
                </span>
              </li>
            );
          })}
        </ul>
      </Card>

      {/* ---------------- Why it matters */}
      <SectionTitle id="neden-onemli">Neden önemli?</SectionTitle>
      <div className="grid gap-4 sm:grid-cols-2">
        {[
          { icon: <DnaIcon />, title: "Biyologlar için", text: "Hangi barkod bölgesinin hangi aile ve cinste işe yaradığını görmek, yeni çalışmaların hangi bölgeyi seçeceğine karar vermeye yardım eder." },
          { icon: <ShieldIcon />, title: "Koruma için", text: <>Yalnızca Türkiye&apos;de yetişen <Term id="endemik">endemik</Term> türlerin barkodu eksikse, bu bilgi başka bir ülkenin verisinden tamamlanamaz. Eksikleri görmek ilk adımdır.</> },
          { icon: <LeafIcon />, title: "Tür tanımak için", text: "Elinizdeki bir bitki parçasının DNA dizisini referanslarla karşılaştırmak, tanıma çalışmasına bir ipucu sağlayabilir. Kesin tanı için yine uzman gerekir." },
          { icon: <GapIcon />, title: "Gelecek çalışmalar için", text: "Hangi türlerin dizisinin henüz okunmadığı bilinirse, saha ve laboratuvar çalışmaları bu boşlukları doldurmaya yönlendirilebilir." },
        ].map((c) => (
          <Card key={c.title} className="flex gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-link">{c.icon}</span>
            <div>
              <h3 className="font-serif text-lg font-semibold">{c.title}</h3>
              <p className="mt-1 text-stone-700">{c.text}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* ---------------- Who is it for */}
      <SectionTitle id="kimler-icin">Kimler için?</SectionTitle>
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { title: "Öğrenciler ve öğretmenler", text: "DNA barkodunun ne olduğunu örneklerle öğrenin; sözlük ve \"Nasıl okunur?\" kutuları derse eklenebilecek açıklamalar sunar.", href: "/sozluk", cta: "Sözlüğe git" },
          { title: "Biyologlar", text: "Aile ve cins bazında ayırt etme sonuçlarına, dizilerin erişim numaralarına ve yönteme ait ayrıntılara ulaşın.", href: "/yontem", cta: "Yöntemi incele" },
          { title: "Meraklı yurttaşlar", text: "Bir bitkinin adını yazın; ne kadar DNA verisi olduğunu, kimlerle akraba göründüğünü ve neden bazı türlerin eksik olduğunu görün.", href: "/turler", cta: "Bir tür ara" },
        ].map((c) => (
          <Card key={c.title} className="flex flex-col">
            <h3 className="font-serif text-lg font-semibold">{c.title}</h3>
            <p className="mt-1 flex-1 text-stone-700">{c.text}</p>
            <Link href={c.href} className="mt-3 inline-flex min-h-11 items-center font-medium text-link underline">{c.cta} →</Link>
          </Card>
        ))}
      </div>

      <Purpose>
        Türkiye&apos;nin bitki çeşitliliğini DNA düzeyinde daha iyi tanımak: hangi türler kısa barkodlarla ayırt edilebiliyor, hangilerinin verisi hâlâ eksik; bunları herkesin görebilmesi.
      </Purpose>
      <p className="mt-6 text-sm text-stone-600">
        Tür listesi WCVP (Kew), diziler ENA/INSDC kayıtlarına dayanır; hatalı tanımlanmış kayıtlar içerebilir. Sonuçlar araştırma amaçlıdır, tahmin niteliğindedir ve uzman doğrulaması yoktur.
      </p>
    </div>
  );
}
