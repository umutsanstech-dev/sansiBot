@echo off
REM run_windows klasorunden proje kokune gec (main.py, .venv burada)
cd /d "%~dp0.."
echo ============================================
echo   Sansi Bot - Calistir
echo ============================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\pip.exe" install playwright --quiet 2>nul
    ".venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo Bot starting...
    ".venv\Scripts\python.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\pip.exe" install playwright --quiet 2>nul
    "venv\Scripts\python.exe" -m playwright install chromium 2>nul
    echo Bot starting...
    "venv\Scripts\python.exe" main.py
) else (
    py -3 -m pip install playwright --quiet 2>nul
    py -3 -m playwright install chromium 2>nul
    echo Bot starting...
    py -3 main.py
)

if errorlevel 1 (
    echo.
    echo HATA: Greenlet DLL hatasi aliyorsaniz:
    echo 1) fix_greenlet.bat calistirin (bir kez)
    echo 2) Hala hata varsa fix_vcredist.bat - VC++ Redistributable yukleyin
    echo.
)
pause
