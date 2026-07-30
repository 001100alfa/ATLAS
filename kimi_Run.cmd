@echo off
rem ATLAS - Kimi CLI baslatici (thin shim: tools/agents/kimi.cmd sarmalayicisi).
rem Sarmalayici tam env kurulumunu yapar: proje-yerel HOME/XDG,
rem KIMI_CLI_GIT_BASH_PATH (2026-07-28 pinleme), ensure-ollama.
rem Kok launcher yalniz PATH + cwd + call.
setlocal enableextensions
set "H=%~dp0"

if not exist "%H%tools\agents\kimi.cmd" (
    echo [HATA] tools\agents\kimi.cmd yok. Kurulum: setup-acp-agents.cmd
    exit /b 1
)

rem --- ATLAS launcher'lari PATH'e (kimi oturumundan atlas komutlari cagirilabilsin) ---
set "PATH=%H%;%PATH%"

rem --- Calisma dizini depo koku ---
cd /d "%H%"

call "%H%tools\agents\kimi.cmd" %*
exit /b %ERRORLEVEL%
