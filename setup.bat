@echo off
rem Sentinel on Windows, one command. Works from PowerShell, cmd or a double-click, and avoids the
rem "running scripts is disabled on this system" error by bypassing the policy for this one process only.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 pause
