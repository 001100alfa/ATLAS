# 034.1 — Ship

## Sonuç
- **`_find_hook_shell()`** yardımcısı: Windows'ta `sh.exe` bulur;
  Non-Windows'ta `"sh"` sabiti döner (POSIX standart).
- **Arama sırası (Windows):**
  1. **Depo-yerel** `tools/git/usr/bin/sh.exe` (2026-07-28 taşınabilir
     kurulum kalıbı) — makine-özel yollara bel bağlamaz.
  2. `PATH` (`shutil.which("sh")`, `shutil.which("sh.exe")`).
  3. Klasik Git for Windows kurulum yolları
     (`%ProgramFiles%\Git\usr\bin\sh.exe`,
     `%ProgramFiles(x86)%\Git\usr\bin\sh.exe`,
     `%LOCALAPPDATA%\Programs\Git\usr\bin\sh.exe`).
  4. Bulunamazsa `None`.
- **`atlas hooks install`** shell None ise install BAŞARILI (exit 0)
  ama **stderr'e uyarı**: "Windows'ta sh.exe bulunamadı — hook
  çalıştırılamaz. Git for Windows kurun veya tools/git/usr/bin/sh.exe
  ile taşınabilir git ekleyin."
- **`atlas hooks status`** iki yeni alan: `shell_available: bool`
  + `shell_path: str | None`. JSON çıktısı içerir; insan formatta
  `shell:` satırı.
- **Bit-uyumluluk:** shell varsa install çıktısı + exit kodu birebir
  korundu (mevcut 034 testleri geçmeye devam ediyor).

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_find_hook_shell
                                            (Non-Windows 'sh', Windows
                                             depo-yerel öncelik + PATH +
                                             klasik yollar);
                                            _cmd_hooks_install shell None
                                              → stderr uyarı;
                                            _cmd_hooks_status shell_available
                                              + shell_path alanı + insan
                                              format satırı; erken return'ler
                                              elif zincirine birleştirildi)
tests/test_cli_hooks.py                   (edit: +7 test 034.1:
                                            find_shell x3 (non-Windows /
                                            depo-yerel / bulunamadı),
                                            install shell yok/var,
                                            status JSON/insan shell alanları)
pipeline/tasks/034-1-windows-ps-hook/*.md (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_hooks_install`, `_cmd_hooks_status`, `_cmd_hooks_uninstall`
  imza + exit kodu KORUNDU (install shell yoksa hâlâ exit 0).
- `_is_atlas_hook`, `_resolve_hook_target`, `_hook_template_text`
  değişmedi.
- Yeni env DEĞİL, yeni exit kodu YOK.
- JSON şeması EKLEMELER (`shell_available`, `shell_path`); eski
  alanlar aynen.

## Kalite kapıları
- pytest: **663 passed + 12 skipped** (656 → +7)
- coverage: %90.98 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/034.1-windows-ps-hook` — main üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## PowerShell wrapper neden YAPILMADI (kararın kısası)
Git hooks mekanizması `.git/hooks/pre-commit` dosyasını
platform-özel bir yorumlayıcı ile çağırır: Unix'te `sh`, Windows'ta
`sh.exe` (git-bash gönderir). PowerShell'in doğrudan bir giriş
noktası YOK — git PS scriptini hook olarak çağırmaz. Yani PS
wrapper bir çözüm olamaz; git'in kendisi sh üstünde. Alternatif:
kullanıcı Git for Windows'u kurar (git-bash getirir), veya
depo-yerel `tools/git/`'i ekler.

## Kullanım örneği
```bash
$ atlas hooks status
=== ATLAS hooks — durum ===
  şablon: tools/hooks/pre-commit (var)
  hedef: /home/user/ATLAS/.git/hooks/pre-commit
    durum: kurulu değil
  shell: /usr/bin/sh                    # Linux/macOS
# veya Windows:
  shell: C:\Users\...\tools\git\usr\bin\sh.exe   # depo-yerel öncelik

# Shell yoksa:
$ atlas hooks install
hooks: kuruldu -> .git/hooks/pre-commit
[!] Windows'ta sh.exe bulunamadı — hook çalıştırılamaz. Git for
    Windows kurun (git-bash) veya tools/git/usr/bin/sh.exe ile
    taşınabilir git ekleyin.
```
