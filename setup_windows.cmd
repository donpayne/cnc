@echo off
rem Lets setup_windows.ps1 run by double-click, since Windows blocks unsigned PowerShell scripts by default.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
if errorlevel 1 pause
