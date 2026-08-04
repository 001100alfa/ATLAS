# Görev 057 — İhtiyaç

`atlas doctor --json` snapshot alma yeteneği var (SPEC 021.1) ama iki
snapshot arasındaki değişimi görmek için manuel `jq` / diff işlemi
gerek. CI regresyon için:
- "Bu PR yeni bir doctor uyarısı oluşturdu mu?" sorusuna cevap gerekli
- Kaç quality alanı iyileşti / kötüleşti — trend takibi

## Kabul kriteri

- `atlas doctor --diff BASELINE_JSON` yeni bayrak.
- Delta şeması (JSON çıktı — `--json` ile):
  - `warnings_added`: current'te var, baseline'da yok (sorted)
  - `warnings_removed`: baseline'da var, current'te yok (sorted)
  - `quality_deltas`: `{field: {before_warning, after_warning, change}}`
    - `change`: `regressed` | `resolved` | `changed` | `appeared` | `disappeared`
    - `unchanged` alanları raporda YER ALMAZ (gürültü azalt)
  - `has_regression`: bool (yeni uyarı VEYA regressed VEYA appeared+warning)
  - `has_improvement`: bool (kaldırılan uyarı VEYA resolved VEYA disappeared)
  - `schema_version_baseline` / `_current`: değişiklik bilgisi
- İnsan çıktısı: ASCII-only marker'lar (`[+]`, `[-]`, `[!]`, `[~]`) —
  Windows cp1254 stdout capture uyumu.
- `--strict + has_regression=True` → exit 9 (SPEC 032 kalıbı).
- Semantik mutex (exit 2):
  - `--diff + --serve` — serve blocking, diff tek-sefer.
  - `--diff + --schema` — schema statik, diff dinamik. Ancak schema
    kısa devre önce çalıştığından pratikte `--diff` erişmiyor →
    `rc in (0, 2)` kabul (test bu şekilde).
  - `--diff + --format prometheus` — prometheus snapshot, delta değil.
- `--diff + --json` ORTOGONAL (delta JSON çıktısı).

## Exit kodları

- 0: başarılı (delta boş VEYA regresyon YOK VEYA `--strict` YOK)
- 2: baseline yok / bozuk JSON / kök obje değil / semantik mutex
- 9: `--strict` + regresyon var

## Riskli

- Windows cp1254 stdout: pytest capsys `→ ⚠ ✓ ✗` gibi Unicode >0xFF
  karakterleri encode edemez → ASCII-only marker'lar (`[+] [-] [!]
  [~]`) kullanıldı.
- `--diff + --serve` sıralaması: --serve önce kontrol ediliyordu →
  HTTP server başlayıp test hang. Çözüm: --diff kontrolü --serve'den
  ÖNCE (semantik mutex early check).
- warnings duplicate sayımı: `set` farkı ile dedup edilir (aynı warning
  2 kez baseline'da olsa bile bir kez raporlanır).
