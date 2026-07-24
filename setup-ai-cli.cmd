@echo off
rem ATLAS — taşınabilir yedek AI CLI kurulumu. İNTERNET GEREKİR.
rem Kurar: OpenCode + Kilo + Cline (npm), Kimi (pip), Goose (Windows binary).
rem Hepsi proje-yerel; sonra setup-acp-agents.cmd ile Juggler'a kaydedin.
setlocal
set "H=%~dp0"
set "AICLI=%H%tools\ai-cli"

rem --- Python bul (kimi + goose extract icin): once gomulu, sonra sistem ---
set "PY=%H%runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/3] npm CLI'lar (OpenCode + Kilo + Cline)...
where npm >nul 2>&1 || ( echo [HATA] npm bulunamadi. Node.js gerekli. & exit /b 1 )
pushd "%AICLI%" || exit /b 1
call npm install --no-fund --no-audit || ( popd & exit /b 1 )
popd

echo [2/3] Kimi ^(pip, py-venv^)...
if not exist "%AICLI%\py-venv\Scripts\kimi.exe" (
  "%PY%" -m venv "%AICLI%\py-venv" || ( echo [HATA] venv olusturulamadi. & exit /b 1 )
  "%AICLI%\py-venv\Scripts\python.exe" -m pip install --quiet kimi-cli || ( echo [HATA] kimi kurulamadi. & exit /b 1 )
)

set "GOOSE_VERSION=1.44.0"
echo [3/3] Goose ^(Windows binary v%GOOSE_VERSION%^)...
set "GEXE=%H%tools\goose\goose-package\goose.exe"
if not exist "%GEXE%" (
  set "GZIP=%TEMP%\goose-win-msvc.zip"
  curl -sL -o "%TEMP%\goose-win-msvc.zip" "https://github.com/block/goose/releases/download/v%GOOSE_VERSION%/goose-x86_64-pc-windows-msvc.zip" || ( echo [HATA] goose indirilemedi. & exit /b 1 )
  if not exist "%H%tools\goose" md "%H%tools\goose"
  "%PY%" -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "%TEMP%\goose-win-msvc.zip" "%H%tools\goose" || ( echo [HATA] goose acilamadi. & exit /b 1 )
)

echo.
echo Kurulum tamam. Kullanim:
echo   opencode_Run.cmd / kilo_Run.cmd      ^(dogrudan CLI^)
echo   setup-acp-agents.cmd                 ^(Juggler ACP Agents: 5 ajan^)
