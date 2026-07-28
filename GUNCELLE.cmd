@echo off
rem ============================================================
rem  ATLAS - SIMDI GUNCELLE
rem  Normalde gerek yok: BASLAT.cmd gunde bir kez kendisi denetler.
rem  Bu dosya "beklemeden simdi bak" demektir.
rem  Panel ikilisi (juggler) burada da OTOMATIK KURULMAZ - yalniz
rem  bildirilir; kurulumu DOCTOR.cmd'deki guvenli sirayla yapilir.
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

echo Guncellemeler denetleniyor...
"%PY%" -m tools.portable.autoupdate --force
echo.
pause
