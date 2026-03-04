@echo off
chcp 65001 > nul
title Vidra - Building EXE...
color 0A

echo.
echo  =====================================================
echo   Vidra  powered by Sheri
echo   Auto build script
echo  =====================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found!
    echo  Install Python 3.10+ from https://python.org
    echo  Make sure to check "Add Python to PATH"!
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo  [OK] %%i found

:: Install dependencies
echo.
echo  [1/4] Installing packages (customtkinter, yt-dlp, pyinstaller)...
pip install --upgrade customtkinter yt-dlp pyinstaller pillow --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed!
    pause & exit /b 1
)
echo  [OK] Packages installed

:: Download yt-dlp.exe binary for bundling
echo.
echo  [2/4] Downloading yt-dlp.exe to bundle inside the app...
python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe', 'yt-dlp_bundled.exe'); print('[OK] yt-dlp.exe downloaded')"
if not exist yt-dlp_bundled.exe (
    echo  [WARN] Could not download yt-dlp.exe - app will use system yt-dlp
)

echo.
echo  [3/4] Downloading ffmpeg.exe (may take 1-2 min)...
python download_ffmpeg.py
if not exist ffmpeg_bundled.exe echo  [WARN] ffmpeg not bundled - install from ffmpeg.org

:: Build the EXE
echo.
echo  [4/4] Building EXE with PyInstaller...
echo.

set EXTRA_BINS=
if exist yt-dlp_bundled.exe set EXTRA_BINS=%EXTRA_BINS% --add-binary "yt-dlp_bundled.exe;."
if exist ffmpeg_bundled.exe  set EXTRA_BINS=%EXTRA_BINS% --add-binary "ffmpeg_bundled.exe;."

set EXTRA_BINS=%EXTRA_BINS% --add-binary "vidra_logo_48.png;." --add-binary "vidra_logo.png;."

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Vidra" ^
    --icon "vidra.ico" ^
    %EXTRA_BINS% ^
    app.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build FAILED! See errors above.
    pause & exit /b 1
)

:: Cleanup temp files
if exist yt-dlp_bundled.exe del yt-dlp_bundled.exe
if exist ffmpeg_bundled.exe  del ffmpeg_bundled.exe
if exist Vidra.spec        del Vidra.spec
if exist build               rmdir /s /q build

echo.
echo  =====================================================
echo   BUILD COMPLETE!
echo.
echo   Your app is ready:  dist\Vidra.exe
echo   Double-click it to run!
echo  =====================================================
echo.

explorer dist
pause
