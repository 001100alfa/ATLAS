@echo off
rem ============================================================
rem  ATLAS — Kurulum Sihirbazi
rem  Bu dosyaya CIFT TIKLAYIN. Baska hicbir sey kurmaniza gerek yok.
rem  Tarayicinizda adim adim bir kurulum ekrani acilir.
rem ============================================================
setlocal enableextensions
title ATLAS - Kurulum Sihirbazi
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
  echo.
  echo   Bu paket normalde kendi Python'unu icerir:
  echo     runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe
  echo   Dosya yoksa paket eksik indirilmis olabilir; ATLAS'i yeniden indirin.
  echo   Alternatif: python.org adresinden Python 3.12 kurun.
  echo.
  pause
  exit /b 1
)

echo.
echo   ATLAS Kurulum Sihirbazi baslatiliyor...
echo   Tarayiciniz birazdan acilacak. Bu pencereyi KAPATMAYIN.
echo   (Kapatmak icin: Ctrl+C)
echo.

"%PY%" -X utf8 -m tools.setup_gui.server
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo   [HATA] Sihirbaz beklenmedik sekilde kapandi ^(kod %RC%^).
  echo   Yardim icin bu penceredeki mesaji paylasin.
  echo.
  pause
)
endlocal
