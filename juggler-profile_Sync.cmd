@echo off
rem ============================================================
rem  ATLAS — Juggler profilini kur/tazele
rem
rem  ATLAS'in Juggler'a kattigi HER SEY juggler-profile\ altinda durur:
rem  eklentiler, ACP ajanlari, MCP sunuculari, komutlar, skills.
rem  Bu betik onlari calisma dizinine (juggler-profile\home) kurar;
rem  baslaticilar JUGGLER_CONFIG_DIR ile Juggler'i oraya yonlendirir.
rem
rem  Juggler klasoru silinip yeniden kurulsa da profil ayakta kalir.
rem  Cift tiklayabilirsiniz. Baslaticilar bunu kendiliginden cagirir.
rem
rem  Kullanim:
rem    juggler-profile_Sync.cmd            kur/tazele
rem    juggler-profile_Sync.cmd /verify    yalniz denetle, yazma
rem    juggler-profile_Sync.cmd /quiet     ciktisiz (baslaticilar icin)
rem ============================================================
setlocal enableextensions
cd /d "%~dp0"

set "ARGS="
set "QUIET="
if /i "%~1"=="/verify" set "ARGS=--verify"
if /i "%~1"=="/quiet" set "QUIET=1"

rem --- Python bul: gomulu > runtime venv > .venv > sistem ---
set "PY="
set "EMB=%~dp0runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe"
if exist "%EMB%" set "PY=%EMB%"
if not defined PY if exist "%~dp0runtime\venv\Scripts\python.exe" set "PY=%~dp0runtime\venv\Scripts\python.exe"
if not defined PY if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"

if not defined PY (
  if not defined QUIET (
    echo   [HATA] Python bulunamadi - profil senkronu yapilamadi.
    echo   Once SETUP.cmd ile kurulumu tamamlayin.
    pause
  )
  exit /b 1
)

if defined QUIET (
  "%PY%" -X utf8 -m tools.juggler_profile.sync %ARGS% >nul 2>&1
  exit /b %ERRORLEVEL%
)

"%PY%" -X utf8 -m tools.juggler_profile.sync %ARGS%
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo   [UYARI] Profil senkronu sorunlu bitti ^(kod %RC%^).
)
rem Cift tiklamayla acildiysa pencere kapanmasin.
echo Kapatmak icin bir tusa basin.
pause >nul
endlocal & exit /b %RC%
