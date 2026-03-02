@echo off
REM run_windows klasorunden proje kokune gec (main.py, .venv burada)
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
    echo.
    echo Bot starting...
    ".venv\Scripts\python.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    echo [1/2] Greenlet fix...
    "venv\Scripts\pip.exe" uninstall -y greenlet 2>nul
    "venv\Scripts\pip.exe" install greenlet --force-reinstall --no-cache-dir
    echo [2/2] Dependencies check...
    "venv\Scripts\pip.exe" install playwright --quiet
    "venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo.
    echo Bot starting...
    "venv\Scripts\python.exe" main.py
) else (
    echo [1/2] Greenlet fix...
    py -3 -m pip uninstall -y greenlet 2>nul
    py -3 -m pip install greenlet --force-reinstall --no-cache-dir
    echo [2/2] Dependencies check...
    py -3 -m pip install playwright --quiet
    py -3 -m playwright install chromium 2>nul
    echo.
    echo Bot starting...
    py -3 main.py
)

if errorlevel 1 (
    echo.
    echo HATA: Greenlet DLL hatasi - Visual C++ Redistributable gerekli!
    echo.
    echo Cozum: run_windows\fix_vcredist.bat calistirin, sonra run.bat tekrar deneyin.
    echo Veya manuel indirin: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
)
pause
