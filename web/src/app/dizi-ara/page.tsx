import type { Metadata } from "next";
import SequenceSearch from "@/components/SequenceSearch";
import { PageTitle } from "@/components/ui";
import { getMeta } from "@/lib/data.server";

export const metadata: Metadata = { title: "Dizi ara" };

export default function SequenceSearchPage() {
  const markers = Object.keys(getMeta().markers);
  return (
    <div>
      <PageTitle title="Dizi arama">
        Bir DNA dizisini yapıştırın; tarayıcınız onu seçtiğiniz markerin referans dizileriyle karşılaştırıp en
        benzer eşleşmeleri gösterir.
      </PageTitle>
      <p className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
        Gizlilik: yapıştırdığınız dizi hiçbir yere gönderilmez ve saklanmaz; karşılaştırma tamamen tarayıcınızda yapılır (yalnızca referans dizi dosyaları sunucudan indirilir).
      </p>
      <SequenceSearch markers={markers} />
    </div>
  );
}
