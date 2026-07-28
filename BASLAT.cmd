@echo off
rem ============================================================
rem  ATLAS - TEK TIKLA BASLAT
rem  Klasoru baska bir Windows bilgisayara kopyaladiysaniz da
rem  yapmaniz gereken tek sey budur: bu dosyaya cift tiklayin.
rem  Yeni makineye uyarlama, guncelleme ve panel acilisi otomatiktir.
rem ============================================================
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

rem Konsol UTF-8 (Turkce karakterler bozulmasin).
chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

rem --- Python bul: once depo icindeki gomulu yorumlayici -------
set "PY="
for /d %%d in ("%ROOT%\runtime\python\cpython-*") do if exist "%%d\python.exe" set "PY=%%d\python.exe"
if not defined PY if exist "%ROOT%\runtime\venv\Scripts\python.exe" set "PY=%ROOT%\runtime\venv\Scripts\python.exe"
if not defined PY if exist "%ROOT%\.venv\Scripts\python.exe" set "PY=%ROOT%\.venv\Scripts\python.exe"
if not defined PY (
  where py >nul 2>&1 && set "PY=py"
)
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo.
  echo Python bulunamadi. Tasinabilir yorumlayici klasorde olmali:
  echo   %ROOT%\runtime\python\
  echo Yoksa setup-portable.cmd calistirin ^(cevrimdisi kurulum^).
  echo.
  pause
  exit /b 1
)

"%PY%" -m tools.portable.start %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Beklenmedik cikis kodu: %RC%
  pause
)
exit /b %RC%
