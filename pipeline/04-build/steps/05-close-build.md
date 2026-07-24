# 05 — Build Kapanışı  `/close-build`

**Amaç:** BUILD log'u tamamlayıp test aşamasına devretmek.

| | |
|---|---|
| **Girdi** | Tüm WP'ler kapalı |
| **Çıktı** | BUILD-XXX.log.md final |

## Prosedür
1. Log tablosunu doldur: süreler, sorunlar, çözümler.
2. hooks'un son lint+test çıktısını yapıştır.
3. Yarım kalan/ertelenen iş varsa AÇIKÇA listele -> 05-test'e.

## Kapıya Katkısı
Aşama şeffaf biter; test aşaması sürprizsiz başlar.
