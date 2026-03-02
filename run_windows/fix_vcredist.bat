@echo off
cd /d "%~dp0"
echo ============================================
echo   Visual C++ Redistributable Kurulumu
echo ============================================
echo.
echo Greenlet DLL hatasini cozmek icin VC++ Redistributable gereklidir.
echo Indiriliyor...
echo.

set "VCREDIST=%~dp0vc_redist.x64.exe"
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%VCREDIST%' -UseBasicParsing"
if errorlevel 1 (
    echo Indirme basarisiz. Manuel indirin:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    start https://aka.ms/vs/17/release/vc_redist.x64.exe
    pause
    exit /b 1
)

echo Kurulum baslatiliyor...
echo Kurulum penceresinde "Yukle" veya "Install" tiklayin.
echo.
start /wait "" "%VCREDIST%"

del "%VCREDIST%" 2>nul
echo.
echo Kurulum tamamlandi. Simdi run.bat calistirin.
pause
