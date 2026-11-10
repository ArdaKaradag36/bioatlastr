# `genera_unresolved` ne anlama gelir?

`sequence_source.json` / `meta.json` → `sequence_meta.genera_unresolved` listesi, WCVP’den gelen **bütün** cins adı dizgilerini (kabul edilmiş cinsler **ve** yalnızca eş ad olarak geçen cins adları) ENA takson kimliğine bağlayamadığımız kayıtları tutar.

Tam koşu (2026-11-03 ENA çekimi) sayıları:

| Küme | n |
|---|---:|
| ENA’da çözülemeyen toplam (`genera_unresolved`) | 1911 |
| Bunlardan kabul edilmiş cins (`accepted_genera_without_ena_taxon`) | 10 |
| Bunlardan yalnızca eş ad cins (`synonym_only_genera_without_ena_taxon`) | 1901 |

Bu yüzden 1911 “Türkiye florasında DNA’sı olmayan kabul edilmiş cins” değildir; büyük çoğunluk sinonim cins adlarıdır. Site metni (`/yontem`) bu ayrımı kullanır.
