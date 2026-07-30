@echo off
rem ATLAS - Kilo CLI baslatici (thin shim: tools/agents/kilo.cmd sarmalayicisi).
rem Sarmalayici tam env kurulumunu yapar: proje-yerel HOME/USERPROFILE/XDG_*,
rem node -> node_modules\@kilocode\cli\bin\kilo direkt cagri (npm shim USERPROFILE'i
rem yutuyordu - 2026-07-24 fix). Kok launcher yalniz PATH prefix + cwd + call.
rem
rem SPEC 035: 14-15. tur launcher kalibiyla simetri. Tarihsel yazim HOMEDRIVE/
rem HOMEPATH override iceriyordu; tools/agents/kilo.cmd bunu yapmaz ama Node
rem os.homedir() USERPROFILE'a bakar (HOMEDRIVE/HOMEPATH ise cmd yerlesigi,
rem Node onlari okumaz). Yani USERPROFILE + HOME yeter.
setlocal enableextensions
set "H=%~dp0"

if not exist "%H%tools\agents\kilo.cmd" (
    echo [HATA] tools\agents\kilo.cmd yok. Kurulum: setup-acp-agents.cmd
    exit /b 1
)

rem --- ATLAS launcher'lari PATH'e (kilo oturumundan atlas komutlari cagirilabilsin) ---
set "PATH=%H%;%PATH%"

rem --- Calisma dizini depo koku ---
cd /d "%H%"

call "%H%tools\agents\kilo.cmd" %*
exit /b %ERRORLEVEL%
