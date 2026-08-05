# Görev 065 — İhtiyaç

Arşiv büyüdükçe (10+ tar), bir dosyanın hangi görevde olduğunu bulmak zor
oluyor. Mevcut yol: `for f in archive/*.tar.gz; do tar tzf $f | grep X; done`
— ATLAS içine gömülmesi mantıklı.

## Kabul

- `atlas archive --search PATTERN [--json] [--archive-root]`.
- Tar dosyaları AÇILMAZ — sadece `getnames()` metadata (hızlı, güvenli).
- Regex `re.search` (part-match); büyük/küçük harf duyarlı (default);
  kullanıcı `(?i)` ile bypass eder.
- Sonuç: `[{archive, matches: [...]}]` — deterministik sıra (archive alfabetik,
  matches sorted).
- Bozuk .tar.gz → atlanır (best-effort).
- Regex geçersiz → exit 2 SPEC HATASI.
- Archive kökü yok → exit 2.
- `--json` bit-hassas JSON çıktı.

## Not

- İnsan çıktısında ASCII-only ("arsivde", SPEC 057 cp1254 dersi).
