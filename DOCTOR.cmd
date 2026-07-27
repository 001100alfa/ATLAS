@echo off
rem ============================================================
rem  ATLAS — Saglik ve Guncelleme Ajani
rem  Bu dosyaya CIFT TIKLAYIN.
rem  Tarayicida acilan ekran: neyin guncel oldugunu, neyin bozuk
rem  oldugunu ve her sorunun kaynagi ile cozumunu gosterir.
rem ============================================================
setlocal enableextensions
title ATLAS - Saglik ve Guncelleme Ajani
cd /d "%~dp0"

rem --- Python bul: once depoya gomulu olan, sonra venv, sonra sistem ---
set "PY="
set "EMB=%~dp0runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe"
if exist "%EMB%" set "PY=%EMB%"
if not defined PY if exist "%~dp0runtime\venv\Scripts\python.exe" set "PY=%~dp0runtime\venv\Scripts\python.exe"
if not defined PY if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"

if not defined PY (
  echo.
  echo   [HATA] Python bulunamadi.
  echo   Once SETUP.cmd ile kurulumu tamamlayin.
  echo.
  pause
  exit /b 1
)

echo.
echo   Saglik ve Guncelleme Ajani baslatiliyor...
echo   Tarayiciniz birazdan acilacak. Bu pencereyi KAPATMAYIN.
echo   (Kapatmak icin: Ctrl+C)
echo.

"%PY%" -X utf8 -m tools.doctor_gui.server
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo   [HATA] Ajan beklenmedik sekilde kapandi ^(kod %RC%^).
  echo.
  pause
)
endlocal
