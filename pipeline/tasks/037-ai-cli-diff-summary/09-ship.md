# 037 — Ship

## Sonuç
- **`atlas ai-cli diff-summary`** yeni alt-komut: `tools/ai-cli/
  package-lock.json` git diff'ini parse eder, tek satır commit
  mesaj önerisi basar (`chore(ai-cli): opencode-ai 1.18.8 → 1.18.9`).
- **`ai-cli` alt-grubu:** gelecekte `ai-cli update` / `ai-cli list`
  gibi eklenebilir; `diff-summary` ilk komut.
- **Parse akıllı:** `node_modules/` prefix strip edilir; birden çok
  paket bump'ı noktalı virgülle ayrılır.
- **Fail-safe:** git yok / repo değil / dosya yok → `(diff okunamadı:
  <sebep>)` + exit 0. Kullanıcı commit mesajını elle yazabilir.
- **Kullanım:**
  ```bash
  $ atlas ai-cli diff-summary
  chore(ai-cli): opencode-ai 1.18.8 → 1.18.9

  $ git commit tools/ai-cli/package-lock.json -m "$(atlas ai-cli diff-summary)"
  ```

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +subprocess import;
                                            +_AI_CLI_PACKAGE_LOCK sabiti;
                                            +_run_git_diff_package_lock,
                                            +_parse_package_lock_diff,
                                            +_format_bumps,
                                            +_cmd_ai_cli_diff_summary;
                                            parser ai-cli alt-grup +
                                            diff-summary)
tests/test_cli_ai_cli.py                  (yeni, +10 test 037:
                                            parse x3, format x3, cmd x4)
pipeline/tasks/037-ai-cli-diff-summary/*.md (2 artefakt)
```

## Sözleşme değişmezliği
- Mevcut CLI komutları KORUNDU; `ai-cli` yeni alt-grup.
- Yeni env DEĞİL, yeni exit kodu YOK.
- `_cmd_scan`, `_cmd_hooks_*`, `_cmd_doctor` dokunulmadı.
- `atlas-portable.json` auto-update mekanizması dokunulmadı — bu
  komut kullanıcı tarafında (commit disiplini) yardım.

## Kalite kapıları
- pytest: **693 passed + 12 skipped** (683 → +10)
- coverage: %91.10 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/037-ai-cli-diff-summary` — 032.5 üstünde tek commit.

## Neden `→` (unicode ok işareti)
Git commit mesajlarında yaygın kalıp (`^` prefix'li changelog'larda
görülür). ASCII `->` da doğru olurdu ama unicode daha temiz. Konsol
UTF-8 (`sys.stdout.reconfigure`) mevcut turlarda zaten var.

## Sözleşme yolu (`ai-cli commit-msg` yerine `ai-cli diff-summary`)
İsim tercihi: `diff-summary` daha genel — sadece commit için değil,
kullanıcı hangi paketin bump olduğunu görmek isteyebilir. Commit
mesajı formatı bir kullanım kalıbı, başka çıktı biçimleri (JSON?)
gelecekte eklenebilir. `commit-msg` çok dar tanımlar.
