# Görev 159 — İhtiyaç

SPEC 134 `doctor --schema --format prometheus --out --gzip` zaten
uygulanmıştı. SPEC 155 (archive) ve SPEC 156 (ai-cli status) için
eklediğim edge kanıt testleri (parent auto-mkdir, .gz idempotent
suffix, stdout↔file satır-bazında eşitlik) doctor için de gerek —
kalıp simetri + regresyon kilidi.

## Kabul

- Envanter doğrulaması: SPEC 134 kalıbı yalnız --schema modunda
  çalışıyor, mevcut mypy/ruff/scan/test geçiyor. **Eksik kod YOK.**
- +4 ekstra kanıt test (SPEC 155/156 kalıbı doctor için):
  1. Parent auto-mkdir (nested dizin — mkdir kalıbı doğrulaması).
  2. Zaten `.gz` uzantısı varsa ikinci `.gz` eklenmez (idempotent suffix).
  3. Stdout ↔ dosya içerik satır-bazında eşitlik (bit-uyumluluk
     zaten SPEC 134'de gzip decompress ile var; SPEC 159 düz
     dosya için ekler — stdout hızlı karşılaştırma).
  4. `--gzip` `--out` olmadan tam SPEC HATASI mesajı (hem
     `--gzip` hem `--out` err içinde geçmeli).
- Yeni CLI kodu YOK — yalnız test ekleme (canlı kanıt).
