import type { Metadata } from "next";
import { Suspense } from "react";
import TreeExplorer from "@/components/TreeExplorer";
import { PageTitle } from "@/components/ui";
import { getFamilies, getMeta } from "@/lib/data.server";

export const metadata: Metadata = { title: "Filogenetik ağaçlar" };

export default function TreesPage() {
  const families = getFamilies();
  const markers = Object.keys(getMeta().markers);
  return (
    <div>
      <PageTitle title="Filogenetik ağaçlar">
        Her aile ve marker için ayrı bir komşu birleştirme (neighbor-joining) ağacı kuruldu; tek bir dev ağaç
        yok. Sürükleyerek kaydırın, tekerlekle yakınlaştırın, bir türü seçip konumunu görün.
      </PageTitle>
      {/* useSearchParams needs a Suspense boundary in statically generated pages */}
      <Suspense fallback={<p className="text-stone-500">Yükleniyor…</p>}>
        <TreeExplorer families={families} markers={markers} />
      </Suspense>
    </div>
  );
}
