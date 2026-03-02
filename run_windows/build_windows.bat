@echo off
cd /d "%~dp0"
echo ============================================
echo   Sansi Bot - Windows EXE Build
echo ============================================
echo.

py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo HATA: Python bulunamadi! Python 3.10+ yukleyin.
        pause
        exit /b 1
    )
    set "PY_CMD=python"
) else (
    set "PY_CMD=py -3"
)

echo [1/6] Sanal ortam olusturuluyor...
if exist "venv_build" rmdir /s /q venv_build
%PY_CMD% -m venv venv_build
call "%~dp0venv_build\Scripts\activate.bat"

echo [2/6] Bagimliliklar yukleniyor...
"%~dp0venv_build\Scripts\pip.exe" install --upgrade pip
"%~dp0venv_build\Scripts\pip.exe" install playwright pyinstaller

echo [3/6] Greenlet duzeltmesi...
"%~dp0venv_build\Scripts\pip.exe" uninstall -y greenlet 2>nul
"%~dp0venv_build\Scripts\pip.exe" install greenlet --force-reinstall --no-cache-dir

echo [4/6] Chromium indiriliyor (~150MB)...
"%~dp0venv_build\Scripts\python.exe" -m playwright install chromium

echo [5/6] EXE olusturuluyor...
"%~dp0venv_build\Scripts\pyinstaller.exe" -y build.spec

echo [6/6] Temizlik...
rmdir /s /q venv_build 2>nul

echo.
echo ============================================
echo   Build tamamlandi!
echo ============================================
echo.
echo EXE: dist\SansiBot.exe
echo.
pause
