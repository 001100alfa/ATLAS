# 004 — Test Raporu

| Metrik | Değer |
|---|---|
| Toplam pytest | **267/267** ✅ (250 + 17 in-process) |
| Yeni test | 29 (12 handler + 6 subprocess e2e + 17 in-process cli) |
| Not | 3 test paralellenmiş sayıldı (test_workflow_audit_verify vb. iki komut çalıştırır) |
| Coverage | **%95** (gate ≥ %90) |
| mypy --strict | 24 dosya temiz |
| ruff | temiz |
| Regresyon | test_platform + test_cli + tüm 002 testleri korundu |

## Kabul Kriterleri
| # | Test | Durum |
|---|---|---|
| AC1 mini.yaml happy | `test_workflow_mini_happy` | ✅ |
| AC2 bilinmeyen handler | `test_workflow_bilinmeyen_handler` | ✅ |
| AC3 gate başarısız | `test_workflow_gate_basarisiz` | ✅ |
| AC4 pytest dry-run | `test_workflow_dry_run_pytest_calismaz` | ✅ |
| AC5 archive dry-run | `test_archive_dry_run_dosyaya_dokunmaz` | ✅ |
| AC6 CLI regresyon | `test_run_echo_demo_regresyon` + platform | ✅ |
| AC7 audit-verify | `test_workflow_audit_verify` | ✅ |
| AC8 coverage %90 | 95% ✅ | ✅ |
