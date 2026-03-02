@echo off
chcp 65001 >nul
echo ============================================
echo   Greenlet DLL Hatasi Duzeltmesi
echo ============================================
echo.

REM Sanal ortam varsa aktive et
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Greenlet kaldiriliyor ve yeniden yukleniyor...
pip uninstall -y greenlet 2>nul
pip install greenlet --force-reinstall --no-cache-dir

echo.
echo Tamamlandi. Simdi "run.bat" veya "python main.py" calistirabilirsiniz.
echo.
echo Hala hata aliyorsaniz Visual C++ Redistributable yukleyin:
echo https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
pause
