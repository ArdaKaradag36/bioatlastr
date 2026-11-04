import type { Metadata } from "next";
import { Suspense } from "react";
import TreeExplorer from "@/components/TreeExplorer";
import { PageIntro, PageTitle, Purpose } from "@/components/ui";
import { getFamilies, getMeta } from "@/lib/data.server";

export const metadata: Metadata = { title: "Filogenetik ağaçlar" };

export default function TreesPage() {
  const families = getFamilies();
  const markers = Object.keys(getMeta().markers);
  return (
    <div>
      <PageTitle eyebrow="Ağaçlar" title="Akrabalık ağaçları">
        Dizilerin birbirine benzerliğini dallanan bir ağaç olarak görün. Aile ve barkod bölgesi seçin, bir türü vurgulayıp yakınlarını bulun.
      </PageTitle>
      <PageIntro
        what={<p>Seçtiğiniz ailedeki DNA dizilerinin, seçtiğiniz barkod bölgesine göre nasıl gruplandığını gösteren ağaç. Her aile ve bölge için ayrı bir ağaç kuruldu; tek bir dev ağaç yoktur.</p>}
        how={<p>Birbirine yakın yapraklar benzer dizilerdir. Aşağıdaki &quot;Nasıl okunur?&quot; kutusunda çizgilerin, renklerin ve iki görünümün anlamı anlatılıyor. Sürükleyerek kaydırın, +/− ile yakınlaştırın ya da klavyede ok tuşlarını kullanın.</p>}
      />
      {/* useSearchParams needs a Suspense boundary in statically generated pages */}
      <Suspense fallback={<p className="text-stone-600">Yükleniyor…</p>}>
        <TreeExplorer families={families} markers={markers} />
      </Suspense>
      <Purpose>
        Dizilerin benzerliğine bakarak, hangi türlerin birbirinden kolay, hangilerinin zor ayrıldığını görmek; yani kısa barkodların nerede işe yaradığını gözle görülür kılmak.
      </Purpose>
    </div>
  );
}
