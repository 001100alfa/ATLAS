@echo off
rem ATLAS — OpenCode CLI (taşınabilir yedek AI kodlama ajanı).
rem Claude Code limitinde veya tercihe göre. Config/data XDG ile proje-içine
rem yönlendirilir (kullanıcı ~/.config'ine dokunmaz). Kurulum: setup-ai-cli.cmd
setlocal enableextensions
set "H=%~dp0"
set "AICLI=%H%tools\ai-cli"
set "BIN=%AICLI%\node_modules\.bin\opencode.cmd"
if not exist "%BIN%" (
  echo [HATA] OpenCode kurulu degil. Once calistir: setup-ai-cli.cmd
  exit /b 1
)

rem --- XDG (4'lu) -> proje-yerel; OpenCode bu 4'unu de okur ---
set "XDG_CONFIG_HOME=%AICLI%\home\config"
set "XDG_DATA_HOME=%AICLI%\home\data"
set "XDG_STATE_HOME=%AICLI%\home\state"
set "XDG_CACHE_HOME=%AICLI%\home\cache"
for %%D in ("%XDG_CONFIG_HOME%" "%XDG_DATA_HOME%" "%XDG_STATE_HOME%" "%XDG_CACHE_HOME%") do if not exist "%%~D" md "%%~D" >nul 2>&1

rem --- ATLAS launcher'lari PATH'e (opencode ATLAS araclarini kabuktan cagirabilsin) ---
set "PATH=%H%;%PATH%"

"%BIN%" %*
endlocal
