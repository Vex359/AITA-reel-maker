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

REM Schedule a 5-day reminder notification via ntfy.sh
echo.
echo  Scheduling 5-day reminder notification...
python -c "from src.phone_notify import send_phone_notification; import datetime; print(f'Reminder will fire on {(datetime.datetime.now() + datetime.timedelta(days=5)).strftime(\"%%Y-%%m-%%d\")}')"

REM Create Windows scheduled task to send ntfy reminder in 5 days
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set /a "year=%datetime:~0,4%"
set /a "month=%datetime:~4,2%"
set /a "day=%datetime:~6,2%"
set /a "hour=%datetime:~8,2%"
set /a "min=%datetime:~10,2%"

REM Calculate target date (5 days from now) using PowerShell
powershell -NoProfile -Command "$d = (Get-Date).AddDays(5); $dateStr = $d.ToString('yyyy-MM-ddTHH:mm'); $taskXml = [xml]@'<Task xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><CalendarTrigger><StartBoundary>{0}</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers><Actions><Exec><Command>python</Command><Arguments>-c \"from src.phone_notify import send_phone_notification; send_phone_notification(title='Time to Generate Reels!', message='Its been 5 days! Run run_cycle.bat to generate 10 more reels for your Instagram queue.', priority='urgent')\"</Arguments></Exec></Actions><Settings><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>false</Hidden></Settings></Task>'@; $taskXml.Task.Triggers.CalendarTrigger.StartBoundary = $dateStr; Register-ScheduledTask -TaskName 'MinecraftReelReminder' -TaskPath '\MinecraftReels' -Xml $taskXml.OuterXml -Force; Write-Host ('  Reminder scheduled for: ' + $d.ToString('yyyy-MM-dd HH:mm'))"

echo.
pause
