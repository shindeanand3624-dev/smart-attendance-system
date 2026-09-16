@echo off
title SVM Smart Attendance System
color 0A

cd /d C:\Users\DELL\SmartAttendance

echo ==========================================
echo     SVM SMART ATTENDANCE SYSTEM
echo ==========================================
echo.

echo [1/2] Starting Flask server...
start "SVM Flask Server" cmd /k "cd /d C:\Users\DELL\SmartAttendance && call venv\Scripts\activate.bat && python app.py"

echo Waiting for Flask server...
timeout /t 5 /nobreak >nul

echo.
echo [2/2] Starting Cloudflare Tunnel...
start "SVM Cloudflare Tunnel" cmd /k "cd /d C:\Users\DELL\SmartAttendance && .\cloudflared.exe tunnel --url http://localhost:5000"

echo.
echo ==========================================
echo Flask + Cloudflare are starting.
echo Check the Cloudflare window for:
echo https://xxxxx.trycloudflare.com
echo ==========================================
echo.
pause
