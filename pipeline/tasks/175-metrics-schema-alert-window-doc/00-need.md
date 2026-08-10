# Görev 175 — İhtiyaç

SPEC 169 `metrics --alert-window MINUTES` uygulandı ama SPEC 153
`metrics --schema` JSON'ında belgelenmemiş — schema kullanıcısı
`--alert-window`'un varlığını + payload alanlarını (SPEC 032.4
alan-ekleme) koddan öğrenemez.

## Kabul

- `atlas metrics --schema` JSON'a **iki yeni alan** (SPEC 032.4 bit-uyumlu):
  - `alert_options`: liste; her biri `{name, spec, desc}`:
    - `{"name": "--alert PCT", "spec": "029", "desc": ...}`
    - `{"name": "--alert-window MINUTES", "spec": "169", "desc": ...}`
    - `{"name": "--alert-email", "spec": "059", "desc": ...}`
    - `{"name": "--alert-webhook URL", "spec": "064", "desc": ...}`
    - `{"name": "--alert-slack URL", "spec": "068", "desc": ...}`
    - `{"name": "--alert-history [PATH]", "spec": "126", "desc": ...}`
    - `{"name": "--alert-history-show [PATH]", "spec": "132", "desc": ...}`
  - `alert_payload`: alert-history NDJSON + webhook payload'ında
    HANGİ ALANLARIN çıktığını dokümante eder; her biri `{name, type,
    when, spec}`:
    - Mevcut 9 alan (`ts`, `alert`, `hit_ratio_pct`, `threshold_pct`,
      `records`, `tokens_in`, `tokens_out`, `cache_creation`,
      `cache_read`) — her zaman
    - SPEC 169 iki alan (`alert_window_minutes`,
      `alert_window_records`) — yalnız `--alert-window` verildiğinde
- notes: SPEC 169 ve SPEC 175 satırları eklenir.
- Prometheus çıktısına **EKLENMEZ** (SPEC 164 kalıbı — YAGNI, mevcut
  4 metric aile sayısı korunur).
- JSON default AYNI (--format yoksa) + alan-ekleme.
- SPEC 023/029/043/153/157/162/169 mevcut davranışlar BİT-UYUMLU.
