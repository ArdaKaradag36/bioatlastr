import type { Metadata } from "next";
import GlossaryList from "@/components/GlossaryList";
import { PageIntro, PageTitle, Purpose } from "@/components/ui";
import { GLOSSARY } from "@/lib/glossary";
import { num } from "@/lib/format";

export const metadata: Metadata = { title: "Sözlük" };

export default function GlossaryPage() {
  return (
    <div>
      <PageTitle eyebrow="Sözlük" title="Terimler ne demek?">
        Bu sitede geçen her teknik sözcüğün sade Türkçe açıklaması. Açıklamalar, terimlerin <em>bu projede</em> nasıl kullanıldığını anlatır.
      </PageTitle>
      <PageIntro
        what={<p>Sitede kullanılan {num(GLOSSARY.length)} terim ve kısaltmanın tek cümlelik açıklaması; gerektiğinde günlük hayattan bir benzetme.</p>}
        how={<p>Aradığınız sözcüğü kutuya yazın ya da gruplara göz atın. Sitenin diğer sayfalarında noktalı altı çizili her sözcüğe dokunduğunuzda buradaki kısa açıklama açılır ve ilgili kutuya bağlantı verir.</p>}
      />
      <GlossaryList />
      <Purpose>
        DNA barkodu gibi teknik bir konuyu, uzman olmayan herkesin de anlayabilmesi; çünkü sonuçların neden güvenilir ya da sınırlı olduğunu ancak terimleri bilerek yorumlayabiliriz.
      </Purpose>
    </div>
  );
}
