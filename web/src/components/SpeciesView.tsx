"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SequenceViewer from "./SequenceViewer";
import TreeViewer from "./TreeViewer";
import Term from "./Term";
import TreeHelp from "./TreeHelp";
import { Card, Latin, PageIntro, Purpose, SectionTitle } from "./ui";
import { loadSpecies, loadTaxonNames, loadTree } from "@/lib/data.client";
import { DISCRIMINATION, distancePct, num, powoUrl } from "@/lib/format";
import type { SpeciesDetail, TaxonNames, TreeFile } from "@/lib/types";

export default function SpeciesView({
  slug,
  markers,
  hideHeader = false,
}: {
  slug: string;
  markers: string[];
  hideHeader?: boolean;
}) {
  const [data, setData] = useState<SpeciesDetail | null | undefined>(undefined);
  const [error, setError] = useState(false);
  const [chosenMarker, setMarker] = useState<string | null>(null); // set when the user clicks a tab
  const [loadedTree, setLoadedTree] = useState<TreeFile | null>(null);
  const [failedTree, setFailedTree] = useState<string | null>(null);

  const [taxonNames, setTaxonNames] = useState<TaxonNames | null>(null);

  useEffect(() => {
    loadSpecies(slug).then(setData).catch(() => setError(true));
    loadTaxonNames().then(setTaxonNames).catch(() => undefined);
  }, [slug]);

  // default tab: the first marker that has sequences
  const firstWithData = data ? markers.find((m) => data.markers[m]?.n_sequences > 0) : undefined;
  const marker = chosenMarker ?? firstWithData ?? markers[0];

  const treeFile = data?.markers[marker]?.tree?.file ?? null;
  useEffect(() => {
    if (!treeFile) return;
    loadTree(treeFile).then(setLoadedTree).catch(() => setFailedTree(treeFile));
  }, [treeFile]);
  // ignore a tree that belongs to another marker (the previous selection)
  const tree = loadedTree && loadedTree.file === treeFile ? loadedTree : null;
  const treeError = failedTree !== null && failedTree === treeFile;

  if (error) return <p className="text-red-700">Tür verisi yüklenemedi. Sayfayı yenileyip tekrar deneyin.</p>;
  if (data === undefined) {
    return hideHeader ? null : <p className="text-stone-600" role="status">Tür bilgileri yükleniyor…</p>;
  }
  if (data === null) {
    return hideHeader ? null : (
      <p className="text-stone-700">
        Bu adda bir tür bulunamadı. <Link className="underline" href="/turler">Tür listesine dön</Link>.
      </p>
    );
  }
  const nAny = markers.reduce((n, m) => n + (data.markers[m]?.n_sequences ?? 0), 0);
  const nTurkey = markers.reduce((n, m) => n + (data.markers[m]?.sequences.filter((x) => x.is_turkey === 1).length ?? 0), 0);
  const nSuspect = markers.reduce((n, m) => n + (data.markers[m]?.sequences.filter((x) => x.suspect).length ?? 0), 0);

  const md = data.markers[marker];
  const namesTr = data.names_tr ?? [];
  const commonNames = [namesTr.slice(0, 3).map((x) => x.n).join(" · "), data.common_name_en].filter(Boolean);
  const genusTr = taxonNames?.genus[data.genus]?.[0]?.n;
  const familyTr = taxonNames?.family[data.family]?.[0]?.n;

  const withData = markers.filter((m) => (data.markers[m]?.n_sequences ?? 0) > 0);
  const without = markers.filter((m) => (data.markers[m]?.n_sequences ?? 0) === 0);
  const list = (a: string[]) => a.join(", ");
  const relMarker = withData.find((m) => data.markers[m].nearest.length > 0);
  const rel = relMarker ? data.markers[relMarker].nearest[0] : null;
  const dstat = DISCRIMINATION[md.discrimination];

  return (
    <div>
      {!hideHeader && (
        <>
          <p className="text-sm text-stone-600">
            <Link className="underline" href="/turler">Türler</Link> / {data.family} / {data.genus}
          </p>
          <h1 className="mt-1 text-3xl font-bold italic text-stone-900 sm:text-4xl">
            {data.name} <span className="font-sans text-xl font-normal not-italic text-stone-600">{data.authorship}</span>
          </h1>
        </>
      )}
      {hideHeader && data.authorship && (
        <p className="mt-1 text-xl font-normal text-stone-600">{data.authorship}</p>
      )}
      <p className="mt-1 text-sm text-stone-600">(<Term id="latince-ad">Latince bilimsel ad</Term>; yanındaki kısaltma adı yayımlayan bilim insanını gösterir)</p>
      {data.endemic === 1 && (
        <p className="mt-2">
          <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800" title="WCVP yayılışı; IUCN veya Türkiye Kırmızı Listesi değil">Türkiye endemiği (WCVP)</span>
        </p>
      )}
      {commonNames.length > 0 && <p className="mt-1 text-lg text-stone-600">{commonNames.join(" · ")}</p>}

      <div className="mt-6">
        <PageIntro
          what={<p>Bu türün DNA barkodu durumu: hangi barkod bölgelerinde dizisi kayıtlı, bu diziler en çok hangi türlere benziyor ve tür akrabalık ağacında nerede duruyor.</p>}
          how={<p>Önce &quot;Bu türün özeti&quot; kutusunu okuyun. Sonra bir barkod bölgesi kutusuna tıklayarak o bölgenin dizilerini, en yakın akrabaları ve ağaçtaki konumu görün. Noktalı altı çizili sözcüklere dokunursanız açıklaması çıkar.</p>}
        />
      </div>

      <Card className="mb-6 border-emerald-400" >
        <h2 className="mb-2 font-serif text-xl font-semibold">Bu türün özeti</h2>
        <ul className="list-disc space-y-2 pl-5 text-stone-800">
          <li>
            <Latin>{data.name}</Latin>, <Term id="familya">{data.family} ailesinin</Term> <Latin>{data.genus}</Latin> <Term id="cins">cinsinde</Term> yer alan bir bitki <Term id="tur">türüdür</Term>.{" "}
            {data.endemic === 1
              ? <>WCVP verisine göre yalnızca Türkiye&apos;de doğal olarak yetişir; yani bir <Term id="endemik">endemik</Term> türdür.</>
              : <>WCVP verisine göre yalnızca Türkiye&apos;ye özgü değildir; başka ülkelerde de doğal olarak yetişir.</>}
          </li>
          {nAny > 0 ? (
            <li>
              <strong>{list(withData)}</strong> barkod bölgesi için toplam {num(nAny)} <Term id="dizi">DNA dizisi</Term> kayıtlıdır;{" "}
              {nTurkey > 0 ? <>bunların {num(nTurkey)} tanesi <Term id="turkiye-ornegi">Türkiye&apos;den toplanan örneklere</Term> aittir.</> : <>hiçbiri Türkiye&apos;den toplanan bir örneğe ait olarak işaretlenmemiştir.</>}
              {without.length > 0 && <> {list(without)} için dizi yoktur.</>}
              {nSuspect > 0 && (
                <> Bu kayıtlardan {num(nSuspect)} tanesi şüpheli işaretlidir (aynı dizi başka bir ailede de var); ayırt etme analizine alınmadı.</>
              )}
            </li>
          ) : (
            <li>
              <strong>Bu tür için henüz DNA barkodu yok.</strong> Bu bir <Term id="veri-boslugu">veri boşluğudur</Term>; türün önemsiz olduğu anlamına gelmez, yalnızca arşivlerde uygun bir dizisi bulunamamıştır.
            </li>
          )}
          {rel && relMarker && (
            <li>
              <strong>{relMarker}</strong> bölgesine göre en yakın akrabası <Link className="text-link underline" href={`/turler/${rel.slug}`}><Latin>{rel.species}</Latin></Link>; aralarındaki{" "}
              <Term id="p-mesafesi">fark</Term> {distancePct(rel.distance)}. Fark ne kadar küçükse diziler o kadar benzerdir; 0 ise bu bölgede hiç fark görünmüyor demektir ve bu bölge yalnızca iki türü ayırmaya yetmez.
            </li>
          )}
          {nAny > 0 && (
            <li>
              Seçili bölgede ({marker}) sonuç: <strong>{dstat.label}</strong>. {dstat.hint}
            </li>
          )}
        </ul>
      </Card>

      <Card className="mt-6">
        <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-stone-600">Aile</dt><dd className="font-medium">{data.family}{familyTr && <span className="font-normal text-stone-500"> ({familyTr})</span>}</dd></div>
          <div><dt className="text-stone-600">Cins</dt><dd className="font-medium italic">{data.genus}{genusTr && <span className="font-normal not-italic text-stone-500"> ({genusTr})</span>}</dd></div>
          <div>
            <dt className="text-stone-600">Türkçe ad</dt>
            <dd className="font-medium">{namesTr.length ? namesTr.slice(0, 3).map((x) => x.n).join("; ") : "kayıtlı değil"}</dd>
          </div>
          <div>
            <dt className="text-stone-600">Kew kaydı (WCVP / POWO)</dt>
            <dd className="font-medium">
              {data.powo_id ? (
                <a className="text-link underline" href={powoUrl(data.powo_id)} target="_blank" rel="noreferrer">
                  POWO kaydı
                </a>
              ) : (
                "—"
              )}
              <span className="font-normal text-stone-500"> · {nAny} dizi{nTurkey > 0 ? `, ${nTurkey} Türkiye örneği` : ""}</span>
            </dd>
          </div>
        </dl>
      </Card>

      {(namesTr.length > 0 || genusTr || familyTr) && (
        <Card className="mt-4">
          <h2 className="mb-2 text-base font-semibold text-stone-800">Türkçe adlar</h2>
          <ul className="space-y-1 text-sm text-stone-700">
            {namesTr.map((x) => (
              <li key={x.n}>
                <span className="font-medium">{x.n}</span>
                {x.a === 1 && <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800">birden fazla türe verilen halk adı</span>}
                <span className="text-stone-500"> — kaynak: </span>
                {x.src.map((s, k) => (
                  <span key={s.l + s.u}>{k > 0 && ", "}<a className="text-link underline" href={s.u} target="_blank" rel="noreferrer">{s.l}</a>{" "}<span className="text-xs text-stone-500" title={s.lic}>[kaynak {s.t} · {s.c === "open" ? "açık lisans" : "ticari olmayan"}]</span></span>
                ))}
              </li>
            ))}
            {(genusTr || familyTr) && (
              <li className="text-stone-600">
                {genusTr && <>Cins adı: <span className="font-medium">{genusTr}</span> </>}
                {familyTr && <>· Aile adı: <span className="font-medium">{familyTr}</span></>}
              </li>
            )}
          </ul>
          <p className="mt-2 text-xs text-stone-500">
            Türkçe adlar açık kaynaklardan (Wikidata, Vikipedi, Catalogue of Life, GRIN, Cichorieae) derlenmiştir; bir uzman tarafından doğrulanmamıştır.{" "}
            <Link className="underline" href="/kaynaklar">Kaynaklar ve lisanslar</Link>
          </p>
        </Card>
      )}

      {nAny === 0 && data.related_with_data && (
        <Card className="mt-6 border-amber-300 bg-amber-50">
          <h2 className="font-serif text-lg font-semibold text-amber-900">Bu tür için ENA/GenBank&apos;ta uygun dizi yok</h2>
          <p className="mt-1 text-sm text-amber-900">Bu bir <Term id="veri-boslugu">veri boşluğudur</Term>; türün önemsiz olduğu anlamına gelmez. Kaydı olan akrabalar, bu türün DNA&apos;sı hakkında dolaylı ipucu verebilir.</p>
          {data.related_with_data.species.length > 0 ? (
            <>
              <p className="mt-1 text-sm text-amber-900">
                Aynı {data.related_with_data.level === "genus" ? "cinsten" : "aileden"} verisi olan türler (dizisi olan akrabalar):
              </p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {data.related_with_data.species.map((r) => (
                  <li key={r.slug}>
                    <Link href={`/turler/${r.slug}`} className="inline-block rounded-lg bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-emerald-50">
                      <span className="italic text-link">{r.name}</span>{" "}
                      <span className="text-stone-600">({r.n_sequences} dizi: {r.markers.join(", ")})</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="mt-1 text-sm text-amber-900">Aynı cins veya ailede de dizisi olan tür bulunamadı: bu bir veri boşluğudur.</p>
          )}
        </Card>
      )}

      {/* marker status */}
      <SectionTitle>Hangi barkod bölgeleri var?</SectionTitle>
      <p className="-mt-2 mb-4 text-stone-700"><Term id="barkod-bolgesi">Barkod bölgelerinden</Term> birine tıklayın; aşağıdaki dizi, akraba ve ağaç bilgisi o bölgeye göre değişir.</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {markers.map((m) => {
          const d = data.markers[m];
          const st = DISCRIMINATION[d.discrimination];
          return (
            <button
              key={m}
              type="button"
              onClick={() => setMarker(m)}
              className={`rounded-2xl border p-4 text-left transition ${
                marker === m ? "border-emerald-600 bg-emerald-50 ring-2 ring-emerald-200" : "border-stone-200 bg-white hover:border-emerald-400"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-serif text-xl font-semibold">{m}</span>
                <span className="text-sm text-stone-700">{num(d.n_sequences)} dizi</span>
              </div>
              <span className={`mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${st.classes}`}>
                {st.label}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mt-8">
        <h2 className="text-2xl font-semibold">{marker} dizileri</h2>
        <p className="mb-3 mt-1 text-stone-700">{DISCRIMINATION[md.discrimination].hint}</p>
        <SequenceViewer species={data.name} marker={marker} records={md.sequences} />
      </div>

      {/* nearest relatives */}
      {md.n_sequences > 0 && (
        <div className="mt-10">
          <h2 className="text-2xl font-semibold">En yakın akrabalar ({marker})</h2>
          <p className="mb-3 mt-1 text-stone-700">
            Aynı ailedeki türler, bu türe en az farklı olandan başlayarak sıralanmıştır. Fark olarak <Term id="p-mesafesi">p-mesafesi</Term> kullanılır: 0, bu bölgede diziler arasında hiç fark olmadığı; sayı büyüdükçe dizilerin daha çok ayrıştığı anlamına gelir.
          </p>
          {md.nearest.length === 0 ? (
            <p className="text-stone-600">Karşılaştırılabilir başka tür bulunamadı.</p>
          ) : (
            <div tabIndex={0} className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
              <table className="w-full text-[0.95rem]">
                <thead className="bg-stone-50 text-left text-stone-600">
                  <tr><th className="p-3">#</th><th className="p-3">Tür</th><th className="p-3"><Term id="p-mesafesi">p-mesafesi</Term> (fark)</th><th className="p-3">Cins</th></tr>
                </thead>
                <tbody>
                  {md.nearest.map((n, i) => (
                    <tr key={n.slug} className="border-t border-stone-100">
                      <td className="p-3 text-stone-500">{i + 1}</td>
                      <td className="p-3"><Link className="italic text-link hover:underline" href={`/turler/${n.slug}`}>{n.species}</Link></td>
                      <td className="p-3 font-mono">{distancePct(n.distance)}</td>
                      <td className="p-3">{n.same_genus ? "Aynı cins" : "Farklı cins"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {md.indistinguishable.length > 0 && (
            <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
              <strong>{marker}</strong> ile bu türden ayırt edilemeyen (mesafe = 0) türler:{" "}
              {md.indistinguishable.map((x, i) => (
                <span key={x.slug}>
                  {i > 0 && ", "}
                  <Link className="italic underline" href={`/turler/${x.slug}`}>{x.species}</Link>
                </span>
              ))}
            </p>
          )}
        </div>
      )}

      {/* tree */}
      <div className="mt-10">
        <h2 className="text-2xl font-semibold">
          {tree?.group.includes("/") ? `${data.genus} cinsi ağacında` : `${data.family} ağacında`} konumu ({marker})
        </h2>
        {md.n_sequences === 0 && <p className="mt-2 text-stone-700">Bu barkod bölgesi için dizi olmadığından tür ağaçta yer almıyor. Bu bir <Term id="veri-boslugu">veri boşluğudur</Term>.</p>}
        {md.n_sequences > 0 && !treeFile && (
          <p className="mt-2 text-stone-700">Bu aile ve barkod bölgesi için ağaç kurmaya yetecek kadar dizi yok.</p>
        )}
        {treeError && <p className="mt-2 text-red-700">Ağaç yüklenemedi.</p>}
        {tree && (
          <>
            <p className="mb-3 mt-1 text-stone-700">
              Kırmızı çizgi bu türün ağaçtaki yerini gösterir. Yakın dallardaki türlerin bu bölgedeki dizileri birbirine benzer. <Term id="hizalama">Hizalama</Term>: <strong>{tree.aligner}</strong>.{" "}
              <Link
                className="text-link underline"
                href={`/agaclar?aile=${data.family}&marker=${marker}&tur=${data.slug}${tree.group.includes("/") ? `&grup=${encodeURIComponent(tree.group)}` : ""}`}
              >
                Tam ekran ağaç sayfasında aç →
              </Link>
            </p>
            <TreeHelp />
            <TreeViewer tree={tree} highlight={data.name} height={460} lockWheel />
          </>
        )}
      </div>

      <Purpose>
        Bu türün DNA barkodunun ne kadar bilindiğini ve komşu türlerden ne kadar ayrılabildiğini göstermek; böylece eksik verilerin nerede olduğu ve nelere dikkat etmek gerektiği anlaşılsın.
      </Purpose>
    </div>
  );
}
