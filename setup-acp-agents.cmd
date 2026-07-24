@echo off
rem ATLAS — Juggler "ACP Agents" için OpenCode + Kilo'yu kaydeder.
rem <project>\.juggler\acp.json üretir (Juggler bunu global config'in üstüne alır).
rem Önce setup-ai-cli.cmd ile CLI'lar kurulu olmalı. Node gerekir.
setlocal
set "H=%~dp0"
where node >nul 2>&1 || ( echo [HATA] node bulunamadi. Node.js gerekli. & exit /b 1 )
if not exist "%H%tools\ai-cli\node_modules" (
  echo [HATA] AI CLI'lar kurulu degil. Once: setup-ai-cli.cmd
  exit /b 1
)

rem PROJ = repo koku (trailing backslash'siz)
set "PROJ=%H%"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"

node "%H%tools\gen-acp-config.js" "%PROJ%" || exit /b 1

echo.
echo Tamam. Juggler'i baslat ^(juggler-desktop_Run.bat / juggler-webui_Run.bat^);
echo model seciciden ACP Agents ^> kilo / opencode gorunur.
