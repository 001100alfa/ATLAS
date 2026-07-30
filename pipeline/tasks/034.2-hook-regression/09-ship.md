# Görev 034.2 — Teslim

`tests/test_cli_hooks_regression.py` — pre-commit shim'i shell
üzerinden gerçek subprocess ile çalıştırıp exit haritasını doğrular.

## Kanıtlar
- Mock atlas exit 0 → shim exit 0
- Mock atlas exit 9 (quality warning) → shim exit 1
- Mock atlas exit 2 (SPEC HATASI) → shim exit 1
- Statik: şablon `atlas doctor --strict --scan-src` içerir, `exit 1`
  + "commit engellendi" mevcut
- Yerelde `_find_hook_shell()` = `tools/git/usr/bin/sh.exe` (Windows
  portable) → 4 canlı test geçti
- +4 test (726 yeşil, cov %90.48)

## Değişmeyen sözleşme
- Kaynak kodda değişiklik YOK — yalnız test eklendi.
- `tools/hooks/pre-commit` şablon dokunulmadı.

## Bilgi
- Baremetal Windows'ta sh.exe yoksa test skip (`pytest.skip`).
- Test tam **entegrasyon** seviyesinde: subprocess + shell + shim +
  mock atlas — 4 halka birden.
