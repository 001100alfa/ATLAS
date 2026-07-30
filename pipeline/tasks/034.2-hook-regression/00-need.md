# Görev 034.2 — İhtiyaç

SPEC 034 hook install/uninstall/status testleri (`test_cli_hooks.py`)
STATIC — script içeriği kontrol edilir ama shim SHELL üzerinden gerçekten
ÇALIŞTIRILMAZ. Windows/Unix ayrımı, `sh.exe` bulunması, quality gate
başarı/başarısızlığı → shim exit haritası CANLI test edilmemişti.

## Kabul kriteri
- Shim, shell üzerinden gerçek subprocess olarak çalıştırılır.
- Mock `atlas` scripti tmpdir/bin'de; env `ATLAS_MOCK_EXIT` shim'in
  çağırdığı `atlas doctor` exit'ini simüle eder.
- Mock exit 0 → shim exit 0.
- Mock exit 9 (drift/scan warning) → shim exit 1.
- Mock exit 2 (SPEC HATASI) → shim exit 1.
- Statik regresyon: şablon `atlas doctor --strict --scan-src` içerir;
  `exit 1` + "commit engellendi" cümlesi mevcut.
- `_find_hook_shell()` None ise test skip (baremetal Windows CI).

## Riskli
- Windows'ta `sh.exe` `tools/git/usr/bin/sh.exe` (taşınabilir) veya
  git-bash'te olabilir. Test skip mekanizması bunu handle eder.
- Mock atlas POSIX sh script — Windows'ta git-bash sh.exe onu çağırır
  (portable). Yerel sh.exe yoksa test skip.
