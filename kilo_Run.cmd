@echo off
rem ATLAS — Kilo CLI (taşınabilir yedek AI kodlama ajanı, Node tabanlı).
rem Claude Code limitinde veya tercihe göre. Config/data XDG ile proje-içine
rem yönlendirilir (kullanıcı ~/.config'ine dokunmaz). Kurulum: setup-ai-cli.cmd
setlocal enableextensions
set "H=%~dp0"
set "AICLI=%H%tools\ai-cli"
set "BIN=%AICLI%\node_modules\@kilocode\cli\bin\kilo"
if not exist "%BIN%" (
  echo [HATA] Kilo kurulu degil. Once calistir: setup-ai-cli.cmd
  exit /b 1
)
where node >nul 2>&1 || ( echo [HATA] node bulunamadi. Node.js gerekli. & exit /b 1 )

rem --- Kilo Windows'ta XDG_* yerine HOME koklu ($HOME/.config/kilo) yollar
rem     kullanir (os.homedir -> USERPROFILE). Portable icin HOME/USERPROFILE ve
rem     HOMEDRIVE/HOMEPATH'i proje-yerele yonlendir. XDG'ler *nix icin de ayarli.
rem     npm .cmd shim'i override'i yutabildigi icin node'u DOGRUDAN cagiriyoruz.
set "KHOME=%AICLI%\home\kilo-home"
if not exist "%KHOME%" md "%KHOME%" >nul 2>&1
set "HOME=%KHOME%"
set "USERPROFILE=%KHOME%"
for %%P in ("%KHOME%") do set "HOMEDRIVE=%%~dP"
for %%P in ("%KHOME%") do set "HOMEPATH=%%~pnxP"
set "XDG_CONFIG_HOME=%KHOME%\.config"
set "XDG_DATA_HOME=%KHOME%\.local\share"
set "XDG_STATE_HOME=%KHOME%\.local\state"
set "XDG_CACHE_HOME=%KHOME%\.cache"

set "PATH=%H%;%PATH%"

node "%BIN%" %*
endlocal
