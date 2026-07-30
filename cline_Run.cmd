@echo off
rem ATLAS - Cline CLI baslatici (thin shim: tools/agents/cline.cmd sarmalayicisi).
rem Sarmalayici tam env kurulumunu yapar: proje-yerel HOME/XDG, CLINE_DIR,
rem node -> node_modules\cline\bin\cline. Kok launcher yalniz PATH + cwd + call.
setlocal enableextensions
set "H=%~dp0"

if not exist "%H%tools\agents\cline.cmd" (
    echo [HATA] tools\agents\cline.cmd yok. Kurulum: setup-acp-agents.cmd
    exit /b 1
)

rem --- ATLAS launcher'lari PATH'e (cline oturumundan atlas komutlari cagirilabilsin) ---
set "PATH=%H%;%PATH%"

rem --- Calisma dizini depo koku ---
cd /d "%H%"

call "%H%tools\agents\cline.cmd" %*
exit /b %ERRORLEVEL%
