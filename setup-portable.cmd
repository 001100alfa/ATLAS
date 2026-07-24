@echo off
rem ATLAS taşınabilir kurulum — OFFLINE. İnternet GEREKMEZ.
rem Gömülü Python'dan relocatable venv üretir ve bağımlılıkları
rem yalnızca vendor\wheels deposundan (--no-index) kurar.
rem Klasör yeni bir makineye kopyalandığında bir kez çalıştırılır.
setlocal
set "ATLAS_HOME=%~dp0"
set "UV=%ATLAS_HOME%runtime\uv.exe"
set "PY=%ATLAS_HOME%runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe"

if not exist "%UV%" ( echo [HATA] runtime\uv.exe yok. Bundle eksik. & exit /b 1 )
if not exist "%PY%" ( echo [HATA] gömülü Python yok. Bundle eksik. & exit /b 1 )

echo [1/2] Relocatable venv olusturuluyor...
"%UV%" venv --relocatable --python "%PY%" "%ATLAS_HOME%runtime\venv" || exit /b 1

echo [2/2] Bagimliliklar OFFLINE kuruluyor (vendor\wheels)...
"%UV%" pip install --python "%ATLAS_HOME%runtime\venv" --no-index ^
  --find-links "%ATLAS_HOME%vendor\wheels" numpy ezdxf pyyaml || exit /b 1

echo.
echo Kurulum tamam. Dene:  atlas-sections i --h 1000 --b 300 --tw 12 --tf 20
