@echo off
rem ATLAS taşınabilir bundle ÜRETİCİ — yalnız bakımcı için, İNTERNET GEREKİR.
rem Gömülü Python 3.12 + uv.exe indirir, wheelhouse'u yeniler.
rem Kullanıcılar bunu çalıştırmaz; setup-portable.cmd yeterlidir.
setlocal
set "ATLAS_HOME=%~dp0"
where uv >nul 2>&1 || ( echo [HATA] Sistemde uv yok. Once uv kurun. & exit /b 1 )

echo [1/3] Portable Python 3.12 indiriliyor...
uv python install 3.12 --install-dir "%ATLAS_HOME%runtime\python" || exit /b 1

echo [2/3] uv.exe projeye kopyalaniyor...
for /f "delims=" %%U in ('where uv') do copy /y "%%U" "%ATLAS_HOME%runtime\uv.exe" >nul

echo [3/3] Wheelhouse yenileniyor...
set "PY=%ATLAS_HOME%runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe"
"%PY%" -m pip download --dest "%ATLAS_HOME%vendor\wheels" numpy>=1.26 ezdxf>=1.3 pyyaml>=6.0 || exit /b 1

echo.
echo Bundle hazir. Offline kurulum icin: setup-portable.cmd
