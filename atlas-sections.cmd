@echo off
rem ATLAS kesit hesap CLI — taşınabilir başlatıcı (gömülü Python + venv).
setlocal
set "ATLAS_HOME=%~dp0"
set "PYTHONPATH=%ATLAS_HOME%src"
set "PYTHONUTF8=1"
"%ATLAS_HOME%runtime\venv\Scripts\python.exe" -m sections.cli %*
