# Görev 052 — İhtiyaç

SPEC 045'te vault verify pre-commit gate'i eklendi. Ama başarısız hook
kullanıcıya "kırık link var" demesi dışında bir şey vermiyor —
kullanıcı raporu görmek için `atlas vault verify` bayraksız çağırmalı
(commit ekranından çıkıp terminale gitmesi lazım).

Auto-dump: hook başarısız olduğunda insanca okunur markdown rapor
otomatik `.atlas/vault-health.md`'e yazılır (git-ignored). Kullanıcı
tek dosyadan tüm bulguları + öneri adımlarını görür.

## Kabul kriteri

- `atlas vault verify --dump-report PATH` yeni bayrağı.
- PATH ebeveyn dizini yoksa `mkdir -p` (best-effort).
- Yazma hatası (OSError) → SESSİZ (verify çıktı sözleşmesi bit-uyumlu;
  hook contextinde commit'i patlatmasın).
- Markdown formatı:
  - Başlık + oluşturma timestamp'i (UTC) + vault yolu + sayaçlar
  - Durum satırı: `durum: ✔ temiz` veya `durum: ❌ bulgu var`
  - Bulgu bölümleri (yalnız dolu olanlar): Kırık linkler / Orfan
    notlar / Orfan taglar
  - Öneri bölümü (yalnız bulgu varsa)
- Bit-uyumluluk:
  - `--json`, `--pretty`, `--strict` bayrakları bit-uyumlu (ortogonal)
  - `--strict + bulgu` → exit 4 (SPEC 042 sözleşmesi korunur)
  - Stdout çıktısı bit-uyumlu (yalnız yan etki: dosya yazımı)
- Hook v3 → v4 yükseltme:
  - Şablon `atlas vault verify --strict --dump-report .atlas/vault-health.md`
  - `_HOOK_SIGNATURE` `v3 → v4`
  - Kullanıcıya stderr'de "Detay rapor: .atlas/vault-health.md (auto-dump)"

## Riskli

- `.atlas/` `.gitignore`'da; commit döngüsü olmaz.
- Yazma sessiz düşüş — kullanıcı bunu doğrulamak isterse `atlas vault
  verify --dump-report /path/olur/mu.md` explicit çağırır.
- Hook v3 → v4: mevcut v3 kullanıcıları `hooks install --force` ile
  güncellemeli (SPEC 045'te de aynı kalıp).
