@echo off
chcp 65001 >nul
title Cumhuriyet Ses Konsolu - Windows EXE olusturucu
cd /d "%~dp0\.."

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")

echo [1/3] Gerekli araclar kuruluyor...
%PY% -m pip install --upgrade pip
%PY% -m pip install PySide6 pyinstaller
if errorlevel 1 ( pause & exit /b 1 )

echo [2/3] Simgeler uretiliyor...
%PY% paket\simge_uret.py

echo [3/3] EXE olusturuluyor... (birkac dakika surebilir)
%PY% -m PyInstaller paket\CumhuriyetSes.spec --noconfirm --clean
if errorlevel 1 ( pause & exit /b 1 )

echo.
echo Bitti!  Tek dosya:  dist\CumhuriyetSesKonsolu.exe
echo Bu dosyayi masaustune kopyalayip cift tiklamak yeterli, Python gerekmez.
pause
