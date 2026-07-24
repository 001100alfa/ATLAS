@echo off
rem ATLAS platform CLI — taşınabilir başlatıcı (gömülü Python + venv).
rem Klasör nereye kopyalanırsa kopyalansın %~dp0 ile göreli çalışır.
setlocal
set "ATLAS_HOME=%~dp0"
set "PYTHONPATH=%ATLAS_HOME%src"
set "PYTHONUTF8=1"
"%ATLAS_HOME%runtime\venv\Scripts\python.exe" -m atlas_core.cli %*
