# Türkiye Bitki DNA Barkod Atlası

**Araştırma projesi** — yapımcılar: **Arda Karadağ** (yazılım) ve **Buse Menekşe** (biyoloji).

Bu depo, başkalarının kendi bilgisayarında kurup çalıştırması için bir yazılım paketi değildir.  
Arda Karadağ ve Buse Menekşe’nin projesinin **kamuya açık çıktısıdır**. Kaynak kod şeffaflık içindir.

**İletişim:** [karadagardaa@gmail.com](mailto:karadagardaa@gmail.com)  
**Site:** [ardakaradag36.github.io/bioatlastr](https://ardakaradag36.github.io/bioatlastr/)  
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

Karadağ, A. & Menekşe, B. (2026). Türkiye Bitki DNA Barkod Atlası (Turkey Plant DNA Barcode Atlas) (version 0.3.0). https://github.com/ArdaKaradag36/bioatlastr

Ayrıca WCVP (Kew) ve kullandığınız dizilerin erişim numaralarına atıf yapın. Ayrıntı: `CITATION.cff`, `DATA_LICENSE.md`.

---

## Yeniden üretim (tam koşu)

Yayımlanan tam koşu girdileri depoda:

| Dosya | İçerik |
|---|---|
| `data/species_full.csv` | WCVP Türkiye kabul edilmiş tür listesi (tam koşu; 10 006 tür) |
| `data/species_meta_full.json` | WCVP sürüm/tarih (`wcvp_file_date`, `downloaded`, sha256, kurallar) |
| `data/config_full.yaml` | Tam koşuda kullanılan `pipeline/config.yaml` kopyası |

```bash
# örnek: izole tam koşu dizini (BARCODE_RUN_DIR); önce WCVP zip + ENA önbelleği gerekir
cp data/config_full.yaml pipeline/config.yaml   # gerekirse
BARCODE_RUN_DIR=runs/full python pipeline/run_all.py --config pipeline/config.yaml
```

**Bu makinede / klonda genelde eksik olanlar:** `data/raw/wcvp.zip` (veya indirme), `data/cache/` (ENA HTTP önbelleği), tam hizalamalar (`runs/full/data/alignments/`, gitignore’da `runs/`), MAFFT ikilisi, isteğe bağlı NCBI e-posta/`NCBI_API_KEY` (varsayılan kaynak ENA; gerekmez). Pilotta `data/species.csv` küçük aile alt kümesidir; tam liste `species_full.csv` içindedir.

### Zenodo’ya arşiv önerisi (yükleme yok)

| Öğe | Yaklaşık boyut | Not |
|---|---:|---|
| `data/species_full.csv` + `species_meta_full.json` + `config_full.yaml` | ~0,7 MB | Zorunlu girdi + sürüm meta |
| `data/synonyms.csv` (tam koşu) | ~1 MB | WCVP eş adlar |
| `results/*.csv` (+ `discrimination_combinations.csv`) | ~birkaç MB | Özet tablolar |
| `web/public/data/stats.json`, `meta.json`, `species_index.json` | ~onlarca MB | Site özeti |
| İsteğe bağlı: `sequence_table.csv` + marker FASTA | ~yüzlerce MB | Ham dizi tablosu |
| İsteğe bağlı: hizalamalar / ağaçlar | ~GB ölçeği | Yeniden üretilebilir; Zenodo kotasına göre seç |

Kod zaten GitHub’da; Zenodo’da sürüm etiketi + yukarıdaki veri paketleri yeterli. `backup-private` ve iNaturalist/IUCN (tier B/C) adları **yüklenmemeli**.

---

## Lisans ve iletişim

- Kod: MIT — telif **Arda Karadağ (GitHub: ArdaKaradag36)** ve **Buse Menekşe**
- Veri tabloları: `DATA_LICENSE.md` (üst kaynaklara atıf)
- Güvenlik / kaldırma: [karadagardaa@gmail.com](mailto:karadagardaa@gmail.com) (`SECURITY.md`)

Site çerez ve izleyici kullanmaz.
