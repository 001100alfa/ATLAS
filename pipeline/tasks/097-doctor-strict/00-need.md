# Görev 097 — İhtiyaç

SPEC 091 `--diff-history-all` toplu diff bilgi komutu — exit 0.
CI/pre-commit için "herhangi tarihçe snapshot'a göre regresyon mu?"
kararı gerek. Şu an regresyon olsa bile exit 0.

## Kabul

- `atlas doctor --diff-history-all --strict`.
- `--strict` yalnız `--diff-history-all` ile birlikte istenen semantik
  (mevcut `--strict` doctor + `--diff` için de kullanılıyor; --diff-
  history-all için de ORTOGONAL geçerli).
- Herhangi snapshot'ta `delta.has_regression == True` → exit 9
  (SPEC 032 kalıbı, SPEC 057 `--diff --strict` ile simetrik).
- Regresyon YOK (tüm snapshot'lar temiz) → exit 0.
- Bilgi çıktısı (tablo/JSON) YİNE basılır; sadece exit code değişir.
- `--json` ile ORTOGONAL — snapshots + delta içeriği AYNI.
- `--strict` VERİLMEZSE SPEC 091 BİT-UYUMLU (exit 0).
