@echo off
rem ============================================================
rem  ATLAS - TASIMA ICIN HAZIRLA
rem  Klasoru RAR'layip baska bir bilgisayara goturmeden ONCE
rem  bunu calistirin: calisan surecleri kapatir (kilitli dosya
rem  arsive yarim girer) ve karsi tarafta kendini uyarlamasi icin
rem  makine parmak izini siler. Hicbir veri silinmez.
rem
rem  Onbellekleri de atmak icin:   PAKETLE.cmd --yagsiz
rem  Dogrudan arsiv uretmek icin:  PAKETLE.cmd --arsiv C:\yol\ATLAS.rar
rem ============================================================
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"
chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

set "PY="
for /d %%d in ("%ROOT%\runtime\python\cpython-*") do if exist "%%d\python.exe" set "PY=%%d\python.exe"
if not defined PY if exist "%ROOT%\runtime\venv\Scripts\python.exe" set "PY=%ROOT%\runtime\venv\Scripts\python.exe"
if not defined PY if exist "%ROOT%\.venv\Scripts\python.exe" set "PY=%ROOT%\.venv\Scripts\python.exe"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Python bulunamadi - BASLAT.cmd icindeki aciklamaya bakin.
  pause
  exit /b 1
)

"%PY%" -m tools.portable.package %*
echo.
pause
