@echo off
rem ATLAS - Goose CLI baslatici (thin shim: tools/agents/goose.cmd sarmalayicisi).
rem Sarmalayici tam env kurulumunu yapar: proje-yerel HOME/APPDATA, ensure-ollama,
rem yerel model varsayilanlari. Kok launcher yalniz PATH prefix + cwd + call.
setlocal enableextensions
set "H=%~dp0"

if not exist "%H%tools\agents\goose.cmd" (
    echo [HATA] tools\agents\goose.cmd yok. Kurulum: setup-acp-agents.cmd
    exit /b 1
)

rem --- ATLAS launcher'lari PATH'e (goose oturumundan atlas komutlari cagirilabilsin) ---
set "PATH=%H%;%PATH%"

rem --- Calisma dizini depo koku ---
cd /d "%H%"

call "%H%tools\agents\goose.cmd" %*
exit /b %ERRORLEVEL%
