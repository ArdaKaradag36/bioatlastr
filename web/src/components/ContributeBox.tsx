import { CONTACT_EMAIL } from "@/lib/site";

export default function ContributeBox({ lang = "tr" }: { lang?: "tr" | "en" }) {
  if (lang === "en") {
    return (
      <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-card" aria-labelledby="contribute-heading">
        <h2 id="contribute-heading" className="font-serif text-xl font-semibold text-stone-900">
          How to contribute / a species has no sequence
        </h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-stone-800">
          <li>
            New DNA barcodes belong in a public INSDC archive (ENA, GenBank or DDBJ), not in an e-mail.
            ENA submission help:{" "}
            <a className="text-link underline" href="https://www.ebi.ac.uk/ena/browser/submit" target="_blank" rel="noreferrer">
              ebi.ac.uk/ena/browser/submit
            </a>
            .
          </li>
          <li>
            To report a wrong record or a site error, write to{" "}
            <a className="text-link underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
          </li>
        </ul>
      </section>
    );
  }
  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-card" aria-labelledby="katki-baslik">
      <h2 id="katki-baslik" className="font-serif text-xl font-semibold text-stone-900">
        Nasıl katkı verilir / eksik bir tür için ne yapılır
      </h2>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-stone-800">
        <li>
          Yeni DNA barkodu e-posta ile değil, herkese açık bir INSDC arşivine (ENA, GenBank veya DDBJ) yüklenir.
          ENA yükleme yardımı:{" "}
          <a className="text-link underline" href="https://www.ebi.ac.uk/ena/browser/submit" target="_blank" rel="noreferrer">
            ebi.ac.uk/ena/browser/submit
          </a>
          . Tür adı WCVP’deki kabul edilmiş adla uyumlu olmalı, erişim numarası yayımlandıktan sonra bu atlas bir sonraki
          ENA yenilemesinde kaydı görebilir.
        </li>
        <li>
          Hatalı bir kayıt, yanlış Türkçe ad veya sitedeki bir yazım için{" "}
          <a className="text-link underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
          {" "}adresine yazın; erişim numarasını ve neyin yanlış olduğunu belirtin.
        </li>
      </ul>
    </section>
  );
}
