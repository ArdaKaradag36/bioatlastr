# Türkiye Bitki DNA Barkod Atlası

**Araştırma projesi** — yapımcılar: **Arda Karadağ** (yazılım) ve **Buse Menekşe** (biyoloji).

Bu depo, başkalarının kendi bilgisayarında kurup çalıştırması için bir yazılım paketi değildir.  
Arda Karadağ ve Buse Menekşe’nin projesinin **kamuya açık çıktısıdır**. Kaynak kod şeffaflık içindir.

**İletişim:** [karadagardaa@gmail.com](mailto:karadagardaa@gmail.com)  
**GitHub:** [ArdaKaradag36/bioatlastr](https://github.com/ArdaKaradag36/bioatlastr)

---

## Değerlendirme için kısa özet

Bu sayfa öğretim üyeleri, danışmanlar ve benzeri değerlendirme için yazılmıştır.  
Teknik yeniden üretim adımları burada yoktur; ayrıntılı teknik rapor istenirse yazarlardan alınır.

**Soru.** Türkiye’de doğal olarak yetişen damarlı bitki türlerini, kısa DNA barkodlarıyla (rbcL, matK, ITS) birbirinden ayırmak mümkün mü? Hangi türlerin halka açık arşivde barkodu yok?

**Ne yaptık.** Kew’in WCVP listesinden Türkiye türlerini aldık. Dizileri ENA / INSDC’den indirdik. Her dizinin en yakın komşusunun aynı türden olup olmadığına baktık. Mesafe eşiği yoktur; uzak da olsa en yakın komşu seçilir. Bir tür, ancak o bölgedeki **bütün** değerlendirilen dizileri bu sınamayı geçerse başarılı sayılır.

**Ne bulduk (yayımlanan veri).** Yaklaşık 10.006 Türkiye türünden 4.087’sinde bu üç bölgeden en az birinde kayıt vardır; 5.919 türde yoktur. Katı tanıma göre tür başarısı kabaca rbcL %26, matK %37, ITS %57’dir (yalnızca birden çok dizisi olan türlerde; karşılaştırma aile veya büyük ailelerde cins içidir). BOLD taranmadı; “eksik” ENA/INSDC’de bulunamama anlamına gelir. 59 dizi, aynı DNA’nın birden fazla aileye atanmış kopyası olduğu için şüpheli işaretlendi ve ayırt etme hesabına alınmadı.

**Sınırlar.** Kayıt adları arşive yükleyen kişiye dayanır. ITS nükleer ve çok kopyalıdır. Karşılaştırma tüm Türkiye florası bir arada değil, aile/cins içindedir. Sonuçlar tahmindir; uzman doğrulaması yoktur. Kesin tür tanısı için kullanılmamalıdır.

**Kim ne yaptı.** Arda Karadağ yazılımı, siteyi ve veri işleme akışını hazırladı. Buse Menekşe biyolojik içeriği ve kontrolü üstlendi.

---

## Atıf

Karadağ, A. & Menekşe, B. (2026). Türkiye Bitki DNA Barkod Atlası (Turkey Plant DNA Barcode Atlas) (version 0.2.0). https://github.com/ArdaKaradag36/bioatlastr

Ayrıca WCVP (Kew) ve kullandığınız dizilerin erişim numaralarına atıf yapın. Ayrıntı: `CITATION.cff`, `DATA_LICENSE.md`.

---

## Lisans ve iletişim

- Kod: MIT — telif **Arda Karadağ (GitHub: ArdaKaradag36)** ve **Buse Menekşe**
- Veri tabloları: `DATA_LICENSE.md` (üst kaynaklara atıf)
- Güvenlik / kaldırma: [karadagardaa@gmail.com](mailto:karadagardaa@gmail.com) (`SECURITY.md`)

Site çerez ve izleyici kullanmaz.
