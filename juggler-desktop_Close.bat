@echo off
rem ATLAS — Juggler Masaustu kapatici. Calisan juggler.exe surecini durdurur.
rem Not: masaustu ve web UI ayni ikilidir (proje basina tek ornek); bu kapatici
rem her iki modu da durdurur.
setlocal
set "KILLED="
taskkill /F /IM juggler-app.exe >nul 2>&1 && set "KILLED=1"
taskkill /F /IM juggler.exe >nul 2>&1 && set "KILLED=1"
if defined KILLED (echo Juggler kapatildi.) else (echo Calisan Juggler bulunamadi.)
endlocal
