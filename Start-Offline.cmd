@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Offline.ps1" -OpenBrowser
if errorlevel 1 pause
