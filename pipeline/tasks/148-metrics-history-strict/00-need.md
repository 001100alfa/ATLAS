# Görev 148 — İhtiyaç

SPEC 132 `--alert-history-show` bilgi komutu her zaman exit 0. CI için
"log dosyasında herhangi alert var mı?" kararını exit code ile döndür
gerek. SPEC 094 (ai-cli --outdated --strict) kalıbı.

## Kabul

- `atlas metrics --alert-history-show --strict`.
- Log dosyasında >=1 kayıt varsa exit 4; boşsa/yoksa exit 0.
- `--strict` yalın (--alert-history-show olmadan) → mevcut SPEC 094
  ai-cli mesajıyla çakışmasın: yalnız `--alert-history-show` bloğunda
  hesaba katılır (bilgi komutu spesifik).
- `--json`/`--format prometheus`/`--out` ile ORTOGONAL (exit code
  değişir, çıktı içeriği AYNI).
- Pretty modda: `SAĞLIK BAŞARISIZ: --strict verildi, N alert kaydı` stderr.
- `--strict` YOKSA SPEC 132 exit 0 AYNI (bit-uyumlu).
