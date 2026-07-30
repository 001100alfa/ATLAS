@echo off
rem ATLAS - OpenCode CLI baslatici (thin shim: tools/agents/opencode.cmd sarmalayicisi).
rem Sarmalayici tam env kurulumunu yapar: proje-yerel XDG_* (config/data/state/cache),
rem native opencode.exe cagrisi. Kok launcher yalniz PATH prefix + cwd + call.
rem
rem SPEC 035: 14-15. tur launcher kalibiyla simetri (opencode/kilo tarihsel
rem yazimlari cekildi -> DRY, kurulum sihirbazi degisikligi otomatik yansir).
setlocal enableextensions
set "H=%~dp0"

if not exist "%H%tools\agents\opencode.cmd" (
    echo [HATA] tools\agents\opencode.cmd yok. Kurulum: setup-acp-agents.cmd
    exit /b 1
)

rem --- ATLAS launcher'lari PATH'e (opencode oturumundan atlas komutlari cagirilabilsin) ---
set "PATH=%H%;%PATH%"

rem --- Calisma dizini depo koku ---
cd /d "%H%"

call "%H%tools\agents\opencode.cmd" %*
exit /b %ERRORLEVEL%
