@echo off
title Minecraft Reel Automation
color 0A

echo.
echo  ========================================
echo   MINECRAFT REEL AUTOMATION
echo  ========================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found in PATH!
    echo  Install Python from python.org
    pause
    exit /b 1
)

REM Check ffmpeg is available
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: ffmpeg not found in PATH!
    echo  Install from ffmpeg.org
    pause
    exit /b 1
)

REM Run the batch generation
echo  Starting batch generation...
echo  This will take 30-60 minutes for 10 reels.
echo.
python -m src.batch_generate

if errorlevel 1 (
    echo.
    echo  ERROR: Batch generation failed!
    echo  Check the output above for details.
) else (
    echo.
    echo  Done! Check your phone for the notification.
)

echo.
pause
