@echo off
cd /d "%~dp0.."
echo ============================================
echo   Sansi Bot - Calistir
echo ============================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo [1/2] Greenlet fix...
    ".venv\Scripts\pip.exe" uninstall -y greenlet 2>nul
    ".venv\Scripts\pip.exe" install greenlet --force-reinstall --no-cache-dir
    echo [2/2] Dependencies check...
    ".venv\Scripts\pip.exe" install playwright --quiet
    ".venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo Bot baslatiliyor...
    ".venv\Scripts\python.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    echo [1/2] Greenlet fix...
    "venv\Scripts\pip.exe" uninstall -y greenlet 2>nul
    "venv\Scripts\pip.exe" install greenlet --force-reinstall --no-cache-dir
    echo [2/2] Dependencies check...
    "venv\Scripts\pip.exe" install playwright --quiet
    "venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo Bot baslatiliyor...
    "venv\Scripts\python.exe" main.py
) else (
    echo [1/2] Greenlet fix...
    py -3 -m pip uninstall -y greenlet 2>nul
    py -3 -m pip install greenlet --force-reinstall --no-cache-dir
    echo [2/2] Dependencies check...
    py -3 -m pip install playwright --quiet
    py -3 -m playwright install chromium 2>nul
    echo Bot baslatiliyor...
    py -3 main.py
)

echo.
if errorlevel 1 (
    echo HATA! fix_greenlet.bat veya fix_vcredist.bat deneyin
)
pause
