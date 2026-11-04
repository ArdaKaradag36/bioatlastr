"""Phase 6 - Turkish TÜBİTAK-style report draft (docs/rapor_taslagi.md), numbers from generated data only.

Usage (from the repository root):  python pipeline/phase6_report.py
"""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from barcode_atlas.paths import DOCS, RESULTS as RES, WEB_DATA as WEB  # noqa: E402

OUT = DOCS / "rapor_taslagi.md"

TODO = "> **[BİYOLOG TARAFINDAN DOLDURULACAK: {}]**\n"


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def pct(x, d=1) -> str:
    return "—" if x is None or x != x else f"%{x * 100:.{d}f}".replace(".", ",")


def table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def main() -> None:
    stats = json.loads((WEB / "stats.json").read_text(encoding="utf-8"))
    meta = json.loads((WEB / "meta.json").read_text(encoding="utf-8"))
    t = stats["totals"]
    markers = list(meta["markers"])
    sp, sq = meta.get("species_meta") or {}, meta.get("sequence_meta") or {}
    partial = bool(meta["families"]) or meta["max_species"]

    mrows = []
    for m in markers:
        s = stats["markers"][m]
        d = s["discrimination"]
        mrows.append({"Marker": m, "Dizi": n(s["sequences"]), "Dizisiz tür": n(s["species_0"]),
                      "Tek dizili tür": n(s["species_1"]), "2+ dizili tür": n(s["species_2plus"]),
                      "Dizi düzeyi başarı": pct(d["success_rate"]), "Tür düzeyi başarı": pct(d["species_success_rate"]),
                      "Mesafesi 0 olan tür çifti": n(s["zero_distance_pairs"])})
    crows = [{"Marker / kombinasyon": c["combination"].replace("+", " + "), "Değerlendirilen tür": n(c["species_evaluated"]),
              "Başarılı": n(c["success"]), "Belirsiz": n(c["ambiguous"]), "Başarısız": n(c["fail"]),
              "Başarı oranı": pct(c["success_rate"])} for c in stats["combinations"]]

    fam = pd.DataFrame([{"Aile": f, "Tür": v["species"], "Dizisi olan tür": v["species_with_any_sequence"]} for f, v in stats["families"].items()])
    fam["Dizisiz tür"] = fam["Tür"] - fam["Dizisi olan tür"]
    top_gap = fam.sort_values("Dizisiz tür", ascending=False).head(10)
    top_cov = fam[fam["Tür"] >= 20].assign(Oran=lambda d: d["Dizisi olan tür"] / d["Tür"]).sort_values("Oran", ascending=False).head(5)
    top_cov["Oran"] = top_cov["Oran"].map(pct)
    gen = pd.DataFrame(stats["genera"])
    gen_gap = gen[gen["species_with_any"] == 0].sort_values("species", ascending=False).head(10)[["genus", "family", "species", "endemic_species"]]
    gen_gap.columns = ["Cins", "Aile", "Tür sayısı", "Endemik tür"]
    pairs = RES / "indistinguishable_pairs.csv"
    n_pairs = len(pd.read_csv(pairs)) if pairs.exists() and pairs.stat().st_size > 5 else 0
    best = max(stats["combinations"], key=lambda c: (c["success_rate"] or 0)) if stats["combinations"] else None

    # ---- caveats with numbers from the data
    fm = pd.read_csv(RES / "discrimination_by_family_marker.csv")
    split_fams = sorted(fm.loc[fm["split_by_genus"].astype(str) == "True", "family"].unique())
    ev = ", ".join(f"{m}: {n(stats['markers'][m]['discrimination']['species_evaluated'])}" for m in markers)
    unm_file = RES / f"unmatched_sample_200.csv"
    unm = ""
    if unm_file.exists():
        u = pd.read_csv(unm_file)
        c = u["class"].value_counts()
        unm = (f"- Eşleşmeyen {n(stats['unmatched_names_total'])} farklı addan rastgele {len(u)} tanesi sınıflandırıldı "
               f"(`scripts/unmatched_sample.py`, `results/unmatched_sample_200.csv`): (a) Türkiye'de doğal olmayan kabul edilmiş tür: "
               f"{int(c.get('a', 0))}; (b) Türkiye türünün eşadı olup eşlenemeyen: {int(c.get('b', 0))}; (c) diğer "
               f"(WCVP'de olmayan ad, sp./cf., başka ülkenin türünün eşadı vb.): {int(c.get('c', 0))}.")
    limits = "\n".join([
        f"- **Başarı yalnızca en az 2 dizisi olan türlerde ölçülür** ({ev} tür; toplam {n(t['species'])} türün küçük bir kısmı). "
        "Tek dizili ya da dizisiz türler başarı oranına girmez; bu türler için oran bilinmemektedir.",
        f"- **Büyük ailelerde karşılaştırma cins içinde yapılmıştır** (bir markerde {n(meta['max_group_sequences'])} diziden fazlası olan aileler: "
        f"{', '.join(split_fams)}); cins içi karşılaştırma ailenin tamamına göre kolaydır, başarı iyimser olabilir. "
        f"{n(stats['groups_skipped'])} grup (çok az dizi ya da tek tür) atlanmış, {n(stats.get('groups_analysed', 0))} grup analiz edilmiştir.",
        f"- **Diziler yalnızca {pct(t['sequences_from_turkey'] / t['sequences'])} oranında Türkiye örneğidir** "
        f"({n(t['sequences_from_turkey'])} / {n(t['sequences'])}); Türkiye popülasyonlarının varyasyonu tam yansımayabilir.",
        f"- **Sürümler:** WCVP dosya tarihi {sp.get('wcvp_file_date', '?')} (indirme {sp.get('downloaded', '?')}); ENA verisi {sq.get('retrieved', '?')} tarihinde alınmıştır.",
        f"- **Yöntem:** p-mesafesine dayalı en yakın komşu (best close match) ve komşu birleştirme (NJ) ağaçları; hizalama: {meta['aligner_label']}.",
        "- Kayıtlardaki tür adları doğrulanmamıştır; yanlış tanımlanmış diziler sonuçları etkileyebilir.",
        f"- Dizisi olmayan tür sayısı {n(t['species_without_sequences'])}, dizisi olmayan endemik tür sayısı {n(t['endemic_without_sequence'])} "
        f"({n(t['endemic_species'])} endemikten); bunlar veri boşluğudur, ayırt edilemez oldukları anlamına gelmez.",
        unm,
        "- Dizi arama sayfası gösterge niteliğindedir; BLAST ve uzman doğrulamasının yerini tutmaz.",
    ])

    md = f"""# Türkiye Bitki Florası için DNA Barkod Atlası — Rapor Taslağı

*Bu taslak `pipeline/phase6_report.py` ile {date.today().isoformat()} tarihinde üretilmiştir. Sayılar yalnızca üretilmiş veriden gelir
(`web/public/data`, `results/`). Köşeli işaretli bölümler biyolog/danışman tarafından doldurulmalıdır.*

{"**UYARI: Bu taslak kısmi bir çalıştırmaya aittir** (aileler: " + ", ".join(meta["families"]) + (f"; en çok {meta['max_species']} tür" if meta["max_species"] else "") + "). Tam çalıştırmadan sonra yeniden üretin." if partial else ""}

## Özet

Bu çalışmada Türkiye florasında doğal olarak yetişen {n(t["species"])} bitki türü ({n(t["families"])} aile, {n(t["genera"])} cins; kaynak: WCVP, Kew) için
kamuya açık DNA barkod dizileri (rbcL, matK, ITS; kaynak: ENA/INSDC) toplanmış, hizalanmış ({meta["aligner_label"]}), komşu birleştirme (NJ)
ağaçları kurulmuş ve her markerin türleri ayırt etme başarısı ölçülmüştür. Türlerin {n(t["species_with_any_sequence"])} tanesinin ({pct(t["species_with_any_sequence"] / t["species"])})
en az bir markerde dizisi vardır; {n(t["species_without_sequences"])} türün hiç dizisi yoktur. {n(t["endemic_species"])} endemik türün {n(t["endemic_without_sequence"])} tanesi
({pct(t["endemic_without_sequence"] / t["endemic_species"] if t["endemic_species"] else None)}) barkod verisinden yoksundur.
{f"En yüksek tür düzeyi ayırt etme başarısı {best['combination'].replace('+', ' + ')} için {pct(best['success_rate'])} ({n(best['species_evaluated'])} değerlendirilen tür) bulunmuştur." if best else ""}

**Anahtar sözcükler:** DNA barkodlama, Türkiye florası, rbcL, matK, ITS, veri boşluğu, endemik türler

## 1. Giriş

{TODO.format("Literatür taraması: DNA barkodlama (CBOL Plant Working Group 2009), rbcL+matK önerisi, ITS'in bitkilerdeki rolü, Türkiye florasının zenginliği ve endemizm, mevcut barkod çalışmaları")}
**Araştırma sorusu:** Kısa bir DNA barkod bölgesi (rbcL, matK, ITS) Türkiye'de yetişen bitki türlerini birbirinden ayırmaya yeter mi? Hangi türler ve
gruplar için veri yoktur?

{TODO.format("Çalışmanın amacı, hipotezler ve özgün değer (öğrenci/danışman)")}

## 2. Yöntem

**Tür listesi.** WCVP (World Checklist of Vascular Plants; dosya tarihi {sp.get("wcvp_file_date", "?")}, indirme {sp.get("downloaded", "?")}) kullanılmıştır. Ölçüt:
{sp.get("rules", "")}. Listede {n(t["species"])} tür vardır; {n(t["endemic_species"])} tanesi endemiktir (yalnızca Türkiye'de doğal).

**Diziler.** ENA Portal ve Browser API'leri kullanılmıştır (erişim tarihi {sq.get("retrieved", "?")}). Sorgular cins bazlıdır (`tax_tree`), kayıt adı WCVP kabul edilmiş
adları ve eş adlarıyla eşleştirilmiştir. Filtreler: sp./cf./aff./melez/UNVERIFIED adların atılması, marker başına uzunluk ve N oranı sınırları, aralık
bölgesi ve genom kayıtlarının atılması, aynı dizinin en çok {meta["max_identical_copies"]} kopyası, tür ve marker başına en çok {meta["max_sequences_per_species_marker"]} dizi
(Türkiye örnekleri öncelikli). Toplam {n(t["sequences"])} dizi tutulmuş, bunların {n(t["sequences_from_turkey"])} tanesi Türkiye'den toplanmıştır.

**Analiz.** Her aile ve marker için hizalama ({meta["aligner_label"]}); {meta["max_group_sequences"]} diziden büyük aileler cins cins analiz edilmiştir.
Mesafe: p-mesafesi (en az {meta["min_overlap"]} ortak baz). Ağaç: NJ. Başarı ölçütü: en yakın komşu (kendisi hariç) aynı türden ise başarılı;
marker kombinasyonları tür düzeyinde, ortak markerların ortalama mesafesiyle değerlendirilmiştir.

{TODO.format("Yöntemin biyolojik gerekçesi ve alternatifler (ör. ML/Bayes ağaçları, BLAST tabanlı kimliklendirme)")}

## 3. Bulgular

### 3.1 Kapsam

{table(pd.DataFrame(mrows))}

![Kapsam](../results/figures/fig1_coverage_by_marker.png)

### 3.2 Ayırt etme başarısı

{table(pd.DataFrame(crows))}

![Başarı](../results/figures/fig2_discrimination_markers_combinations.png)
![Aile düzeyi](../results/figures/fig3_family_success.png)

Mesafesi 0 olan (bu markerle ayırt edilemeyen) tür çifti sayısı: {n(n_pairs)} (`results/indistinguishable_pairs.csv`).
![En yakın akraba mesafeleri](../results/figures/fig5_nearest_relative_distance.png)

### 3.3 Veri boşlukları

En çok dizisiz türü olan 10 aile:

{table(top_gap)}

Kapsamı en yüksek aileler (en az 20 tür):

{table(top_cov)}

Hiç dizisi olmayan en büyük 10 cins ({n(t["genera_without_sequence"])} cinsin hiç dizisi yok):

{table(gen_gap)}

Hiç dizisi olmayan aile sayısı: {n(t["families_without_sequence"])}. Dizisiz endemik tür sayısı: {n(t["endemic_without_sequence"])} (`results/data_gaps_endemics.csv`).
![Veri boşlukları](../results/figures/fig4_data_gaps_families.png)

## 4. Tartışma

{TODO.format("Bulguların yorumu: hangi markerler/kombinasyonlar neden daha iyi ayırıyor; ITS'in melezleşme/çoklu kopya sorunları; düşük başarılı grupların biyolojisi (poliploidi, hızlı radyasyon, introgresyon); literatürle karşılaştırma")}
{TODO.format("Veri boşluklarının nedenleri ve öncelikli toplama hedefleri (endemikler, büyük cinsler)")}

## 5. Sınırlılıklar

{limits}
{TODO.format("Sınırlılıkların biyolojik yorumu ve sonuçlara etkisi (yanlış adlandırılmış kayıtlar, Türkiye dışı popülasyonlar, hızlı evrimleşen gruplar)")}

## 6. Gelecek çalışmalar

- Dizisiz endemik türler için arazi toplaması ve barkodlama {TODO.format("öncelik listesi ve lojistik")}
- Ek markerler (trnH-psbA, trnL-F) ve ML/Bayes ağaçları.
- Fotoğraftan tür tanıma modülünün eklenmesi (site kodu bunun için hazırlanmıştır).
- Ulusal herbaryum örneklerinden doğrulanmış referans kitaplığı.

## Kaynaklar

{TODO.format("Atıf listesi")}
- WCVP: Govaerts R. et al., World Checklist of Vascular Plants, Royal Botanic Gardens, Kew.
- ENA: European Nucleotide Archive, EMBL-EBI (INSDC).
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
