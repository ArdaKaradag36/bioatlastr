"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SequenceViewer from "./SequenceViewer";
import TreeViewer from "./TreeViewer";
import { Card, SectionTitle } from "./ui";
import { loadSpecies, loadTaxonNames, loadTree } from "@/lib/data.client";
import { DISCRIMINATION, distancePct, powoUrl } from "@/lib/format";
import type { SpeciesDetail, TaxonNames, TreeFile } from "@/lib/types";

export default function SpeciesView({ slug, markers }: { slug: string; markers: string[] }) {
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

  if (error) return <p className="text-red-700">Tür verisi yüklenemedi.</p>;
  if (data === undefined) return <p className="text-stone-500">Yükleniyor…</p>;
  if (data === null) {
    return (
      <p className="text-stone-600">
        Bu adda bir tür bulunamadı. <Link className="underline" href="/turler">Tür listesine dön</Link>.
      </p>
    );
  }
  const nAny = markers.reduce((n, m) => n + (data.markers[m]?.n_sequences ?? 0), 0);
  const nTurkey = markers.reduce((n, m) => n + (data.markers[m]?.sequences.filter((x) => x.is_turkey === 1).length ?? 0), 0);

  const md = data.markers[marker];
  const namesTr = data.names_tr ?? [];
  const commonNames = [namesTr.slice(0, 3).map((x) => x.n).join(" · "), data.common_name_en].filter(Boolean);
  const genusTr = taxonNames?.genus[data.genus]?.[0]?.n;
  const familyTr = taxonNames?.family[data.family]?.[0]?.n;

  return (
    <div>
      <p className="text-sm text-stone-500">
        <Link className="underline" href="/turler">Türler</Link> / {data.family} / {data.genus}
      </p>
      <h1 className="mt-1 text-3xl font-bold italic text-stone-900 sm:text-4xl">
        {data.name} <span className="text-xl font-normal not-italic text-stone-500">{data.authorship}</span>
      </h1>
      {data.endemic === 1 && (
        <p className="mt-2">
          <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800">Türkiye endemiği</span>
        </p>
      )}
      {commonNames.length > 0 && <p className="mt-1 text-lg text-stone-600">{commonNames.join(" · ")}</p>}

      <Card className="mt-6">
        <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-stone-500">Aile</dt><dd className="font-medium">{data.family}{familyTr && <span className="font-normal text-stone-500"> ({familyTr})</span>}</dd></div>
          <div><dt className="text-stone-500">Cins</dt><dd className="font-medium italic">{data.genus}{genusTr && <span className="font-normal not-italic text-stone-500"> ({genusTr})</span>}</dd></div>
          <div>
            <dt className="text-stone-500">Türkçe ad</dt>
            <dd className="font-medium">{namesTr.length ? namesTr.slice(0, 3).map((x) => x.n).join("; ") : "kayıtlı değil"}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Kew (WCVP / POWO)</dt>
            <dd className="font-medium">
              {data.powo_id ? (
                <a className="text-emerald-800 underline" href={powoUrl(data.powo_id)} target="_blank" rel="noreferrer">
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
                  <span key={s.l + s.u}>{k > 0 && ", "}<a className="text-emerald-800 underline" href={s.u} target="_blank" rel="noreferrer">{s.l}</a>{" "}<span className="text-xs text-stone-500" title={s.lic}>[kaynak {s.t} · {s.c === "open" ? "açık lisans" : "ticari olmayan"}]</span></span>
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
          <h2 className="text-lg font-semibold text-amber-900">Bu tür için ENA/GenBank&apos;ta uygun dizi yok</h2>
          {data.related_with_data.species.length > 0 ? (
            <>
              <p className="mt-1 text-sm text-amber-900">
                Aynı {data.related_with_data.level === "genus" ? "cinsten" : "aileden"} verisi olan türler (dizisi olan akrabalar):
              </p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {data.related_with_data.species.map((r) => (
                  <li key={r.slug}>
                    <Link href={`/turler/${r.slug}`} className="inline-block rounded-lg bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-emerald-50">
                      <span className="italic text-emerald-800">{r.name}</span>{" "}
                      <span className="text-stone-500">({r.n_sequences} dizi: {r.markers.join(", ")})</span>
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
      <SectionTitle>Hangi barkod markerları var?</SectionTitle>
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
                <span className="text-lg font-semibold">{m}</span>
                <span className="text-sm text-stone-600">{d.n_sequences} dizi</span>
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
        <p className="mb-3 mt-1 text-sm text-stone-500">{DISCRIMINATION[md.discrimination].hint}</p>
        <SequenceViewer species={data.name} marker={marker} records={md.sequences} />
      </div>

      {/* nearest relatives */}
      {md.n_sequences > 0 && (
        <div className="mt-10">
          <h2 className="text-2xl font-semibold">En yakın akrabalar ({marker})</h2>
          <p className="mb-3 mt-1 text-sm text-stone-500">
            Aynı ailedeki türler arasında en küçük p-mesafesine göre sıralıdır (0 = diziler aynı).
          </p>
          {md.nearest.length === 0 ? (
            <p className="text-stone-500">Karşılaştırılabilir başka tür bulunamadı.</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
              <table className="w-full text-sm">
                <thead className="bg-stone-50 text-left text-stone-600">
                  <tr><th className="p-3">#</th><th className="p-3">Tür</th><th className="p-3">p-mesafesi</th><th className="p-3">Cins</th></tr>
                </thead>
                <tbody>
                  {md.nearest.map((n, i) => (
                    <tr key={n.slug} className="border-t border-stone-100">
                      <td className="p-3 text-stone-500">{i + 1}</td>
                      <td className="p-3"><Link className="italic text-emerald-800 hover:underline" href={`/turler/${n.slug}`}>{n.species}</Link></td>
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
        {md.n_sequences === 0 && <p className="mt-2 text-stone-500">Bu marker için dizi olmadığından ağaçta yer almıyor.</p>}
        {md.n_sequences > 0 && !treeFile && (
          <p className="mt-2 text-stone-500">Bu aile ve marker için ağaç kurmaya yetecek (en az 3) dizi yok.</p>
        )}
        {treeError && <p className="mt-2 text-red-700">Ağaç yüklenemedi.</p>}
        {tree && (
          <>
            <p className="mb-3 mt-1 text-sm text-stone-500">
              Kırmızı dal bu türün konumunu gösterir. Hizalama: <strong>{tree.aligner}</strong>.{" "}
              <Link
                className="text-emerald-800 underline"
                href={`/agaclar?aile=${data.family}&marker=${marker}&tur=${data.slug}${tree.group.includes("/") ? `&grup=${encodeURIComponent(tree.group)}` : ""}`}
              >
                Tam ekran ağaç sayfasında aç →
              </Link>
            </p>
            <TreeViewer tree={tree} highlight={data.name} height={460} lockWheel />
          </>
        )}
      </div>
    </div>
  );
}
