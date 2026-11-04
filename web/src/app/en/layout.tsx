import type { Metadata } from "next";
import { PROJECT_TITLE, PROJECT_TITLE_EN } from "@/lib/site";

export const metadata: Metadata = {
  title: `English summary · ${PROJECT_TITLE}`,
  description:
    "A research atlas asking whether short DNA barcodes (rbcL, matK, ITS) can separate the plant species of Turkey. BOLD was not searched.",
  alternates: {
    canonical: "/en",
    languages: { "tr-TR": "/", en: "/en" },
  },
  openGraph: {
    locale: "en_GB",
    title: PROJECT_TITLE_EN,
    url: "/en",
  },
};

export default function EnglishLayout({ children }: { children: React.ReactNode }) {
  return (
    <div lang="en" dir="ltr">
      {children}
    </div>
  );
}
