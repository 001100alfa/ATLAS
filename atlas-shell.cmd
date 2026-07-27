@echo off
rem ============================================================
rem  ATLAS komut satiri - etkilesimli konsol.
rem  Projeyi PATH'e ekler ve acik kalan bir komut penceresi verir;
rem  boylece `atlas ...` / `atlas-sections ...` dogrudan yazilabilir.
rem
rem  NOT: `atlas.cmd`yi argumansiz calistirmak ise yaramaz - argparse
rem  alt komut ister, hata basar ve pencere kapanir. Kullaniciya acik
rem  kalan bir kabuk lazim; bu dosya onu saglar.
rem ============================================================
set "ATLAS_HOME=%~dp0"
if "%ATLAS_HOME:~-1%"=="\" set "ATLAS_HOME=%ATLAS_HOME:~0,-1%"
set "PATH=%ATLAS_HOME%;%PATH%"
cd /d "%ATLAS_HOME%"

rem UTF-8 kod sayfasi: cikti mm^2 / mm^4 gibi ust simgeler iceriyor.
chcp 65001 >nul 2>&1

echo.
echo   ATLAS komut satiri
echo   ------------------------------------------------------------
echo   Kesit hesabi:
echo     atlas-sections i   --h 1000 --b 300 --tw 12 --tf 20
echo     atlas-sections box --h 200  --b 300 --t 10
echo.
echo   Platform:
echo     atlas context "kesit hesabi"      baglam paketi
echo     atlas remember kesit "not"        hafizaya yaz
echo     atlas recall "atalet momenti"     hafizadan ara
echo     atlas scan src                    sir taramasi
echo     atlas audit-verify                denetim zinciri
echo.
echo   Yardim: atlas --help  ^|  atlas-sections --help
echo   Kapatmak icin: exit
echo   ------------------------------------------------------------
echo.

cmd /k
