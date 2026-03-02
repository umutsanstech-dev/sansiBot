@echo off
cd /d "%~dp0.."
echo ============================================
echo   Greenlet DLL Hatasi Duzeltmesi
echo ============================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\pip.exe" uninstall -y greenlet 2>nul
    ".venv\Scripts\pip.exe" install greenlet --force-reinstall --no-cache-dir
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\pip.exe" uninstall -y greenlet 2>nul
    "venv\Scripts\pip.exe" install greenlet --force-reinstall --no-cache-dir
) else (
    py -3 -m pip uninstall -y greenlet 2>nul
    py -3 -m pip install greenlet --force-reinstall --no-cache-dir
)

echo Greenlet yeniden yuklendi.

echo.
echo Tamamlandi. Simdi "run.bat" veya "python main.py" calistirabilirsiniz.
echo.
echo Hala hata aliyorsaniz Visual C++ Redistributable yukleyin:
echo https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
pause
