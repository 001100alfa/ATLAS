@echo off
rem ATLAS — taşınabilir AI CLI kurulumu (OpenCode + Kilo). İNTERNET GEREKİR.
rem Proje-yerel npm kurulumu (global DEĞİL); ikililer tools\ai-cli\node_modules
rem altına iner. Node + npm gerekir. Bir kez çalıştır; sonra opencode_Run.cmd /
rem kilo_Run.cmd ile kullan.
setlocal
set "H=%~dp0"
where npm >nul 2>&1 || ( echo [HATA] npm bulunamadi. Node.js kurulu olmali. & exit /b 1 )

echo AI CLI'lar proje-yerel kuruluyor (tools\ai-cli)...
pushd "%H%tools\ai-cli" || exit /b 1
call npm install --no-fund --no-audit || ( popd & exit /b 1 )
popd

echo.
echo Kurulum tamam. Kullanim:
echo   opencode_Run.cmd   ^(OpenCode^)
echo   kilo_Run.cmd       ^(Kilo^)
