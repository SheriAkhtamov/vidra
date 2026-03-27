@echo off
chcp 65001 > nul
title Vidra - Building Setup Installer...
color 0A

echo.
echo  =====================================================
echo   Vidra  powered by Sheri Akhtamov
echo   Auto build script (STANDARD INSTALLER VERSION)
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
echo  [1/5] Installing packages (customtkinter, yt-dlp, pyinstaller)...
pip install --upgrade customtkinter yt-dlp pyinstaller pillow --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed!
    pause & exit /b 1
)
echo  [OK] Packages installed

:: Download yt-dlp.exe binary for bundling
echo.
echo  [2/5] Downloading yt-dlp.exe to bundle inside the app...
curl.exe -L --silent --show-error --retry 3 -o yt-dlp_bundled.exe "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
if not exist yt-dlp_bundled.exe (
    echo  [WARN] Could not download yt-dlp.exe - app will use system yt-dlp
) else (
    echo  [OK] yt-dlp.exe downloaded
)

echo.
echo  [3/5] Downloading ffmpeg.exe (may take 1-2 min)...
python download_ffmpeg.py
if not exist ffmpeg.exe echo  [WARN] ffmpeg not bundled - install from ffmpeg.org

:: Generate proper icon from vidra_logo_48.png
echo.
echo  Generating icon from vidra_logo_48.png...
python gen_ico.py

:: Build the EXE (folder mode for installer)
echo.
echo  [4/5] Building EXE with PyInstaller (folder mode for installer)...
echo.

set EXTRA_BINS=
if exist yt-dlp_bundled.exe set EXTRA_BINS=%EXTRA_BINS% --add-binary "yt-dlp_bundled.exe;."
if exist ffmpeg.exe  set EXTRA_BINS=%EXTRA_BINS% --add-binary "ffmpeg.exe;."
if exist ffprobe.exe set EXTRA_BINS=%EXTRA_BINS% --add-binary "ffprobe.exe;."

set EXTRA_BINS=%EXTRA_BINS% --add-data "vidra_logo_48.png;." --add-data "vidra_logo.png;." --add-data "vidra.ico;."

pyinstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name "Vidra" ^
    --icon "vidra.ico" ^
    --distpath "dist" ^
    %EXTRA_BINS% ^
    app.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build FAILED! See errors above.
    pause & exit /b 1
)

echo  [OK] Application built successfully

:: Verify PyInstaller output
if not exist "dist\Vidra\Vidra.exe" (
    echo.
    echo  [ERROR] dist\Vidra\Vidra.exe not found after PyInstaller!
    echo  PyInstaller may have failed silently.
    pause & exit /b 1
)

:: Compile Installer
echo.
echo  [5/5] Compiling installer with Inno Setup...

:: Find Inno Setup compiler (flat logic, no nesting)
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if defined ISCC goto :found_iscc

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
if defined ISCC goto :found_iscc

where iscc >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%p in ('where iscc') do set ISCC=%%p
)
if defined ISCC goto :found_iscc

echo.
echo  [ERROR] Inno Setup 6 not found!
echo.
echo  To build the installer, install Inno Setup 6:
echo  https://jrsoftware.org/isdl.php
echo.
echo  The application is ready in dist\Vidra\ folder.
echo  You can run dist\Vidra\Vidra.exe directly (portable),
echo  or install Inno Setup and re-run BUILD.bat for installer.
echo.
explorer dist\Vidra
pause & exit /b 0

:found_iscc
echo  [OK] Inno Setup found: %ISCC%
echo.
"%ISCC%" "installer.iss"

if errorlevel 1 (
    echo  [ERROR] Installer compilation failed!
    pause & exit /b 1
)

:: Cleanup temp files
if exist yt-dlp_bundled.exe del yt-dlp_bundled.exe
if exist ffmpeg.exe  del ffmpeg.exe
if exist ffprobe.exe del ffprobe.exe
if exist Vidra.spec        del Vidra.spec
if exist build               rmdir /s /q build

echo.
echo  =====================================================
echo   BUILD COMPLETE!
echo.
echo   Installer:  dist\Vidra-Setup.exe
echo.
echo   Installs to Program Files, creates Start Menu
echo   shortcuts, registers uninstaller in Windows.
echo  =====================================================
echo.

explorer dist
pause
