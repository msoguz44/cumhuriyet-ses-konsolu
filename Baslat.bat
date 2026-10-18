@echo off
chcp 65001 >nul
title Cumhuriyet Ses Konsolu
cd /d "%~dp0"

rem --- Python bulunuyor ---
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")

%PY% --version >nul 2>nul
if errorlevel 1 (
  echo.
  echo  Python bulunamadi.
  echo  Lutfen once https://www.python.org/downloads/ adresinden Python kurun.
  echo  Kurulum ekraninda "Add Python to PATH" kutusunu isaretlemeyi unutmayin.
  echo.
  pause
  exit /b 1
)

rem --- Gerekli paket kurulu mu? ---
%PY% -c "import PySide6" >nul 2>nul
if errorlevel 1 (
  echo.
  echo  Ilk calistirma: gerekli ses/arayuz paketi kuruluyor, lutfen bekleyin...
  echo.
  %PY% -m pip install --upgrade pip
  %PY% -m pip install PySide6
  if errorlevel 1 (
    echo.
    echo  Kurulum basarisiz oldu. Internet baglantinizi kontrol edip tekrar deneyin.
    pause
    exit /b 1
  )
)

rem --- Uygulamayi penceresiz baslat ---
start "" %PY%w "%~dp0main.py"
exit /b 0
