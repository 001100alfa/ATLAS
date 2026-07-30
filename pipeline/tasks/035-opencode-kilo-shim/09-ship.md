# 035 — Ship

## Sonuç
- **`opencode_Run.cmd` refactor:** thin shim; `tools/agents/opencode.cmd`
  sarmalayıcısını `call` eder. Kendi XDG env satırları kaldırıldı
  (sarmalayıcı bunları zaten yapıyor).
- **`kilo_Run.cmd` refactor:** aynı kalıp; `tools/agents/kilo.cmd`
  sarmalayıcısını `call` eder. Kendi HOME/USERPROFILE/HOMEDRIVE/
  HOMEPATH satırları kaldırıldı; `tools/agents/kilo.cmd` HOME +
  USERPROFILE ile yeter (Node os.homedir() USERPROFILE'a bakar,
  HOMEDRIVE/HOMEPATH cmd yerleşiği — Node onları okumaz).
- **6 kök launcher tam simetri:** hepsi `tools/agents/<name>.cmd`
  üzerine thin shim (PATH + cwd + call + exit code).
- **Kanıt (smoke):**
  - `opencode_Run.cmd --version` → `1.18.8`
  - `kilo_Run.cmd --version` → `7.4.16`

## Dosyalar
```
opencode_Run.cmd                          (rewrite: tarihsel BIN+XDG →
                                            thin shim call tools/agents/
                                            opencode.cmd)
kilo_Run.cmd                              (rewrite: tarihsel node+HOME+
                                            HOMEDRIVE → thin shim call
                                            tools/agents/kilo.cmd)
pipeline/tasks/035-opencode-kilo-shim/*.md (2 artefakt)
```

## Sözleşme değişmezliği
- CLI davranışı (kullanıcının `--version` çıktıları, `opencode` /
  `kilo` alt-komutları) BİREBİR korundu.
- `tools/agents/*.cmd` sarmalayıcıları hiç dokunulmadı (kurulum
  sihirbazı tarafından üretiliyor).
- Ana repo Python kod tabanı etkilenmedi — pytest regresyonu
  aynı (676 passed).

## Kalite kapıları
- pytest: **676 passed + 12 skipped** (regresyon; 032.3'ten değişmedi)
- coverage: %91.17
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı
- Manuel smoke: opencode + kilo `--version` çıktıları temiz.

## Branch
`feat/035-opencode-kilo-shim` — 032.3 üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## Simetri kanıtı (6 launcher = aynı kalıp)
```
opencode_Run.cmd    → tools/agents/opencode.cmd
kilo_Run.cmd        → tools/agents/kilo.cmd
claudecode_Run.cmd  → (özel: where claude — taşınabilirlik istisnası)
goose_Run.cmd       → tools/agents/goose.cmd
cline_Run.cmd       → tools/agents/cline.cmd
kimi_Run.cmd        → tools/agents/kimi.cmd
```
5 launcher `tools/agents/*.cmd` üstüne thin shim; 1 launcher
(claudecode) `where claude` özel çünkü Claude Code taşınabilirlik
istisnasıdır (memory 2026-07-24).

## Bonus not (kapsam dışı)
`opencode_Run.cmd --version` → `1.18.8` gösterdi ama `package.json`
`^1.18.9` (14. tur chore drift). Yani `node_modules/opencode-ai/bin/
opencode.exe` gerçek sürümü package-lock ile senkron değil — `npm
install` çalıştırılmamış. Bu bir başka drift; **035 kapsamı değil**
(launcher refactor). Bir sonraki `BASLAT.cmd` auto-update turu ya da
elle `npm install` bunu düzeltir. Not düşüldü.
