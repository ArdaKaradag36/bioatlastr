import type { Metadata } from "next";
import SpeciesBrowser from "@/components/SpeciesBrowser";
import { PageTitle } from "@/components/ui";
import { getFamilies, getMeta, getStats } from "@/lib/data.server";
import { num } from "@/lib/format";

export const metadata: Metadata = { title: "Türler" };

export default function SpeciesListPage() {
  const families = getFamilies().map((f) => f.family);
  const markers = Object.keys(getMeta().markers);
  const total = getStats().totals.species;
  return (
    <div>
      <PageTitle title="Türler">
        Atlasta {num(total)} tür var. Latince ya da Türkçe adla arayın; ardından türün barkod dizilerini,
        en yakın akrabalarını ve ağaçtaki konumunu görün.
      </PageTitle>
      <SpeciesBrowser families={families} markers={markers} />
    </div>
  );
}
