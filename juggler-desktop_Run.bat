@echo off
rem ATLAS — Juggler Masaustu (native pencere) baslatici.
rem Ayni ikili, --window ile natif WebView2 penceresi acar (tarayici gerekmez).
rem Kapatmak: juggler-desktop_Close.bat
setlocal enableextensions
title ATLAS - Juggler Desktop
set "ATLAS_HOME=%~dp0"
set "PROJ=%ATLAS_HOME%"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"

rem --- juggler.exe bul: JUGGLER_EXE > tools\juggler > PATH ---
set "JX="
if defined JUGGLER_EXE if exist "%JUGGLER_EXE%" set "JX=%JUGGLER_EXE%"
if not defined JX if exist "%ATLAS_HOME%tools\juggler\juggler.exe" set "JX=%ATLAS_HOME%tools\juggler\juggler.exe"
if not defined JX for /f "delims=" %%J in ('where juggler 2^>nul') do if not defined JX set "JX=%%J"
if not defined JX (
  echo [HATA] juggler.exe bulunamadi.
  echo   - Derle:  docs\JUGGLER.md  ^(go build -o juggler.exe .\cmd\juggler^)
  echo   - Yerlestir: tools\juggler\juggler.exe
  echo   - veya JUGGLER_EXE ortam degiskenini ayarla.
  pause
  exit /b 1
)

rem --- masaustu penceresi juggler-app ikilisini gerektirir (JX ile ayni dizin) ---
for %%D in ("%JX%") do set "APPDIR=%%~dpD"
if not defined JUGGLER_APP_BIN if exist "%APPDIR%juggler-app.exe" set "JUGGLER_APP_BIN=%APPDIR%juggler-app.exe"
if not defined JUGGLER_APP_BIN (
  echo [UYARI] juggler-app.exe bulunamadi ^(masaustu penceresi icin gerekli^).
  echo   Derle: go build -o juggler-app.exe .\cmd\juggler-app  -^> tools\juggler\ altina.
  echo   Alternatif: juggler-webui_Run.bat ^(tarayici, bu ikiliye ihtiyac duymaz^).
)

rem --- ATLAS profilini kur/tazele (eklenti, ACP ajanlari, MCP, komutlar, skills) ---
rem Profil depo icinde durur; JUGGLER_CONFIG_DIR ile Juggler oraya bakar. Boylece
rem Juggler klasoru silinip yeniden kurulsa da ATLAS tarafi ayakta kalir.
call "%ATLAS_HOME%juggler-profile_Sync.cmd" /quiet
set "JUGGLER_CONFIG_DIR=%ATLAS_HOME%juggler-profile\home"

rem --- ATLAS launcher'lari PATH'e ---
set "PATH=%ATLAS_HOME%;%PATH%"

echo Juggler Masaustu penceresi aciliyor (proje: %PROJ%)...
"%JX%" --project "%PROJ%" --window --kill-existing
endlocal
