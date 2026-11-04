import Link from "next/link";
import CiteBox from "@/components/CiteBox";
import ContributeBox from "@/components/ContributeBox";
import { Card, PageTitle } from "@/components/ui";
import { getMeta, getStats } from "@/lib/data.server";
import { CONTACT_EMAIL, PROJECT_KIND_EN, PROJECT_TITLE, PROJECT_TITLE_EN, PRODUCERS_EN, REPO_URL } from "@/lib/site";

function n(value: number): string {
  return value.toLocaleString("en-GB");
}

function pctEn(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

export default function EnglishSummaryPage() {
  const stats = getStats();
  const meta = getMeta();
  const t = stats.totals;
  const markers = Object.keys(meta.markers);
  const best = markers
    .map((m) => ({ m, d: stats.markers[m].discrimination }))
    .filter((x) => x.d.species_success_rate != null)
    .sort((a, b) => (b.d.species_success_rate ?? 0) - (a.d.species_success_rate ?? 0))[0];

  return (
    <div>
      <p className="mb-4 text-sm text-stone-600">
        <Link className="underline" href="/">Türkçe ana sayfa</Link>
        {" · "}
        <span>English summary</span>
      </p>
      <PageTitle eyebrow="English summary" title={PROJECT_TITLE_EN}>
        {PROJECT_TITLE}. A {PROJECT_KIND_EN.toLowerCase()} by {PRODUCERS_EN}: can short DNA barcode regions separate the vascular plant species of Turkey, and where are the public-data gaps?
      </PageTitle>

      <Card className="mb-6">
        <h2 className="font-serif text-xl font-semibold">What this is</h2>
        <p className="mt-2 text-stone-800">
          The species list is WCVP (Kew): accepted native species of Turkey. Sequences are from ENA/INSDC only.
          The site reports coverage (which species have a barcode) and a discrimination test (whether those
          barcodes separate species). Results are estimates, not expert-verified identifications.
        </p>
      </Card>

      <Card className="mb-6">
        <h2 className="font-serif text-xl font-semibold">Method in brief</h2>
        <p className="mt-2 text-stone-800">
          Sequences are aligned (MAFFT), compared with p-distance, and tested with a <strong>threshold-free
          nearest-neighbour</strong> rule: the closest sequence is always chosen; there is no distance cutoff and
          no “no match” class. The official species success rule is <strong>strict</strong>: every evaluated
          sequence of a species must neighbour a sequence of the same species. Comparisons are within family
          (or genus in very large families).
        </p>
      </Card>

      <Card className="mb-6">
        <h2 className="font-serif text-xl font-semibold">Limits you should read first</h2>
        <ul className="mt-2 list-disc space-y-2 pl-5 text-stone-800">
          <li>
            <strong>BOLD was not searched.</strong> “Missing” means not found in ENA/INSDC. A BOLD search is planned
            as future work.
          </li>
          <li>
            <strong>Threshold-free nearest neighbour</strong> will pick a neighbour even when it is distant.
          </li>
          <li>
            <strong>ITS is nuclear and multi-copy.</strong> Paralogs and fungal contamination can inflate ITS success.
            The highest strict species success among the three regions is currently {best ? `${best.m} (${pctEn(best.d.species_success_rate)}, n = ${n(best.d.species_evaluated)} species)` : "—"}.
          </li>
          <li>At most {n(meta.max_sequences_per_species_marker)} sequences are kept per species × region.</li>
        </ul>
      </Card>

      <Card className="mb-6">
        <h2 className="font-serif text-xl font-semibold">Numbers</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-stone-800">
          <li>{n(t.species)} species in the WCVP Turkey list; {n(t.species_with_any_sequence)} have at least one barcode sequence ({pctEn(t.species_with_any_sequence / t.species)}).</li>
          <li>{n(t.species_without_sequences)} species have no ENA/INSDC barcode in these three regions.</li>
          <li>{n(t.sequences)} sequences after filters; {n(t.sequences_from_turkey)} are Turkey specimens.</li>
          <li>{n(t.endemic_species)} endemic on WCVP (not a Red List); {n(t.endemic_without_sequence)} of those have no sequence.</li>
          {typeof t.suspect_sequences === "number" && t.suspect_sequences > 0 && (
            <li>{n(t.suspect_sequences)} sequences are flagged suspect (identical DNA assigned to more than one family) and are excluded from discrimination.</li>
          )}
          {markers.map((m) => {
            const d = stats.markers[m].discrimination;
            return (
              <li key={m}>
                {m} strict species success: {pctEn(d.species_success_rate)} (n = {n(d.species_evaluated)}). Comparison is within family/genus.
              </li>
            );
          })}
        </ul>
      </Card>

      <div className="mb-6">
        <CiteBox lang="en" />
      </div>
      <div className="mb-6">
        <ContributeBox lang="en" />
      </div>

      <p className="text-stone-800">
        Producers: {PRODUCERS_EN}. Code and data:{" "}
        <a className="text-link underline" href={REPO_URL}>{REPO_URL}</a>
        . Contact:{" "}
        <a className="text-link underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        . Full method (Turkish): <Link className="text-link underline" href="/yontem">/yontem</Link>.
      </p>
    </div>
  );
}
