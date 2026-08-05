# Görev 088 — İhtiyaç

SPEC 037.2 `ai-cli list` tüm paketleri gösterir. Kullanıcı hangilerinin
güncelleme beklediğini görmek için satır satır bakmak zorunda. Filtre yok.

## Kabul

- `atlas ai-cli list --outdated [--json]`.
- Filtre: `installed is None` VEYA `_strip_semver_prefix(expected) !=
  installed`.
- `--outdated` VERİLMEZSE davranış BİT-UYUMLU (SPEC 037.2 tüm liste).
- JSON şeması AYNI (`path`, `packages[]`); sadece `packages` filtreli.
- Hepsi güncel → JSON `packages: []`, pretty `(guncelleme yok)` (exit 0).
- `_strip_semver_prefix`: `^`, `~`, `>=`, `>`, `=`, boşluk sıyır.
  npm semver-satisfies değil (literal string), SPEC 088 dokümantasyon
  bunu açıkça belirtir; caret/tilde ile major/minor uyumluluğu
  YAKALAMAZ (yanlış pozitif olabilir; kullanıcı fark için `npm outdated`
  çalıştırır).
