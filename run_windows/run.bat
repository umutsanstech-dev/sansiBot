@echo off
cd /d "%~dp0.."
title Sansi Bot

echo ============================================
echo   Sansi Bot - Calistir
echo ============================================
echo Dizin: %CD%
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\pip.exe" install playwright --quiet 2>nul
    ".venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo Bot baslatiliyor...
    ".venv\Scripts\python.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\pip.exe" install playwright --quiet 2>nul
    "venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo Bot baslatiliyor...
    "venv\Scripts\python.exe" main.py
) else (
    echo .venv bulunamadi, sistem Python kullaniliyor...
    py -3 -m pip install playwright --quiet 2>nul
    py -3 -m playwright install chromium 2>nul
    echo Bot baslatiliyor...
    py -3 main.py
)

:end
echo.
if errorlevel 1 (
    echo HATA! Cozum: fix_greenlet.bat veya fix_vcredist.bat
)
echo.
pause
