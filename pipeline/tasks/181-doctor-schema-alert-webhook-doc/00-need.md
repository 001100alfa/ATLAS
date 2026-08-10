# Görev 181 — İhtiyaç

SPEC 168 `doctor --alert-webhook` + SPEC 177 payload `strict` alanı
uygulandı ama SPEC 040 `doctor --schema` JSON'ında BELGELENMEDİ —
schema kullanıcısı payload alanlarını + tetik ölçütünü koddan
öğrenmek zorunda. SPEC 175 metrics `alert_options`/`alert_payload`
kalıbı doctor için de.

## Kabul

- `_doctor_schema_descriptor()` JSON'a **iki yeni alan** (SPEC 032.4
  bit-uyumlu):
  - `alert_options`: liste; her biri `{name, spec, desc}`:
    - `{"name": "--alert-webhook URL", "spec": "168",
       "desc": "quality warning varsa POST"}`
  - `alert_payload`: SPEC 168/177 4 alan; her biri `{name, type, when, spec}`:
    - `{"name": "alert", "type": "str",
       "when": "always", "spec": "168",
       "desc": "sabit 'doctor'"}`
    - `{"name": "warnings", "type": "list[str]",
       "when": "always", "spec": "168",
       "desc": "report.warnings ust duzey liste"}`
    - `{"name": "quality_warnings", "type": "dict[str, str]",
       "when": "always", "spec": "168",
       "desc": "quality.<field> -> warning mesajı"}`
    - `{"name": "strict", "type": "bool",
       "when": "always", "spec": "177",
       "desc": "--strict verildi mi (CI-gate exit 9 tetigi)"}`
- notes: SPEC 168 + SPEC 177 + SPEC 181 satırları eklenir.
- Prometheus çıktısına EKLENMEZ (SPEC 175 YAGNI kalıbı; mevcut 6
  metric aile sayısı korunur).
- JSON default (--format yok) bit-uyumlu; alan-ekleme.
- SPEC 040/128/134/142/166 mevcut şema davranışları AYNI.
