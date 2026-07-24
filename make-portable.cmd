@echo off
rem ATLAS çok-platform taşınabilir bundle ÜRETİCİ — bakımcı için, İNTERNET GEREKİR.
rem Windows/Linux/macOS için dist/atlas-<hedef>/ altında bağımsız ağaçlar üretir.
rem Kullanıcılar bunu çalıştırmaz; hedef makinede setup-portable yeterlidir.
rem
rem   make-portable.cmd                         :: tüm hedefler
rem   make-portable.cmd --targets linux-x86_64  :: seçili hedef
rem   make-portable.cmd --list                  :: hedefleri listele
setlocal
set "H=%~dp0"

rem Yerel bir Python bul: önce gömülü, sonra sistem.
set "PY=%H%runtime\python\cpython-3.12.13-windows-x86_64-none\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%H%tools\make_portable.py" %*
