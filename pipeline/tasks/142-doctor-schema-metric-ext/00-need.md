# Görev 142 — İhtiyaç

SPEC 128 `doctor --schema --format prometheus` 4 metric ailesi
(version + top_level_field + quality_field + exit_code) yayımlıyor.
`_doctor_schema_descriptor()` içinde `backend`, `retry_pricing`,
`storage` alanları da mevcut ama `top_level_field` altında sadece
`type + desc` label'ları var. `backend` ve `retry_pricing` dict
alanların iç anahtarları (env değişkenleri) info-metric olarak
yayımlanmıyor. Dashboard drift takibi için gerek.

## Kabul

- `_doctor_schema_descriptor()` içine 2 yeni alan:
  - `backend_options`: `[{name: "ATLAS_LLM", values: ["stub","anthropic","acp"], desc}]`
  - `retry_pricing_envs`: `[{name: "ATLAS_LLM_RETRIES", desc}, ...]`
- Prometheus çıktısında 2 yeni metric ailesi:
  - `atlas_doctor_schema_backend_option{name, value}` = 1
  - `atlas_doctor_schema_env{group, name}` = 1
- JSON çıktıda yeni alanlar eklenir (BİT-UYUMLU ekleme).
- HELP+TYPE her metric için (SPEC 128 kalıbı).
- 6 metric ailesi (2 yeni) HELP+TYPE sayısı test.
