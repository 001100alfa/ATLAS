@echo off
rem ATLAS — Juggler Web UI baslatici. Sunucuyu baslatir, baglanti URL'sini basar.
rem Tarayicidan acilir (yerel/LAN). Kapatmak: juggler-webui_Close.bat
setlocal enableextensions
title ATLAS - Juggler Web UI
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

rem --- ATLAS eklentisini kur (idempotent kopya; symlink Windows'ta admin ister) ---
set "EXTDIR=%USERPROFILE%\.juggler\extensions\atlas-engineering"
xcopy /E /I /Y /Q "%ATLAS_HOME%integrations\juggler" "%EXTDIR%\" >nul

rem --- ATLAS launcher'lari PATH'e (eklentinin atlas-sections/atlas shell-out'u icin) ---
set "PATH=%ATLAS_HOME%;%PATH%"

echo Juggler Web UI baslatiliyor (proje: %PROJ%)...
echo Asagida yazan URL'yi tarayicida acin. Kapatmak: juggler-webui_Close.bat
"%JX%" --project "%PROJ%" --kill-existing
endlocal
