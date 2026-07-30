# 034.1 — İhtiyaç: Windows sh.exe guard + hook shell tespiti

## Bağlam
034 pre-commit hook (`tools/hooks/pre-commit`) POSIX sh script.
Git hooks Windows'ta git-bash'ten gelen `sh.exe` ile çalıştırılır —
Git for Windows kurulu her makinede standart. Ancak edge case'ler
var:
- Minimal git kurulumu (Portable Git bazı sürümleri) `sh.exe`
  içermeyebilir.
- GitHub Desktop tek başına gömülü git kullanır ama shell yoksa
  hook sessizce çalışmaz — `error: cannot spawn .git/hooks/pre-commit:
  No such file or directory` gibi mesaj git'in içinde kaybolur.

Yani `atlas hooks install` yaparken **shell'in var olup olmadığını
kontrol etmek** ve yoksa açık uyarı basmak lazım. Ayrı PowerShell
wrapper YAGNI — git hooks mekanizması sh üzerine kurulu, PS shim
olamaz. Yalnız guard + tanı.

## İhtiyaç (tek cümle)
`atlas hooks install` Windows'ta iken `sh.exe` PATH'te veya git
kurulumunda yoksa **install BAŞARILI olsun ama stderr'e açık uyarı
bassın**; `atlas hooks status` yeni bir `shell_available` alanı
raporlasın.

## Ölçülebilir Başarı
- **M1 — `_find_hook_shell()` yardımcısı:** Windows'ta `sh.exe`
  arar: `shutil.which("sh")`, `shutil.which("sh.exe")`, klasik
  Git for Windows yolları (`%ProgramFiles%\Git\usr\bin\sh.exe`,
  `%LOCALAPPDATA%\Programs\Git\usr\bin\sh.exe`, `%ProgramFiles(x86)%\
  Git\usr\bin\sh.exe`), depo-yerel taşınabilir (`tools/git/usr/bin/
  sh.exe` — memory 2026-07-28 tasınabilir kurulum). Bulunursa
  mutlak yol, yoksa None. Non-Windows'ta her zaman `"sh"` (POSIX
  standart).
- **M2 — `atlas hooks install` uyarısı:** shell None ise install
  yine tamamlar (exit 0) ama stderr'e Türkçe uyarı: "Windows'ta
  sh.exe bulunamadı; git-bash / Git for Windows kur → hook aksi
  hâlde çalışmaz."
- **M3 — `atlas hooks status` alanı:** `shell_available: bool`,
  `shell_path: str | None`. `--json` çıktısı da içerir.
- **M4 — Bit-uyumluluk:** shell var olan durumda install çıktısı
  ve exit kodu **birebir korunur** (mevcut testler kırılmaz).
- **M5 — Test:** +3-4 test — shell None install uyarısı, shell var
  install temiz, status shell_available alanı, `_find_hook_shell`
  fallback zinciri (mock).
- **M6 — DECISIONS:** [KARAR] neden PS wrapper YAGNI; shell arama
  sırasında depo-yerel `tools/git/` neden önce; Non-Windows davranışı
  neden `"sh"` (path kontrolü değil — POSIX standart).

## Kapsam DIŞI
- Alternative shell (`bash.exe`, `dash.exe`) desteği — YAGNI,
  git-bash `sh.exe` gönderiyor.
- PowerShell wrapper script — git hooks sh üzerine kurulu, PS
  giriş noktası yok.
- Otomatik Git for Windows kurulumu — kullanıcının işi; ATLAS
  tanı verir.
- WSL sh algılama — Windows-native git ile WSL sh uyumsuz;
  kullanıcı Windows git'i mi WSL git'i mi kullanıyor belirsiz.

## Kısıt
- `_cmd_hooks_install`, `_cmd_hooks_status` mevcut çıktı sözleşmesi
  KORUNUR; yalnız EKLEMELER (uyarı + status alanı).
- Yeni exit kodu YOK — install shell yoksa hâlâ exit 0 (uyarı ile).
- `tools/hooks/pre-commit` shim değişmez (POSIX sh script; shell
  varsa çalışır).
- Türkçe uyarı.
