@echo off
chcp 65001 >nul
echo Restoring the ORIGINAL Age of Empires II HD AI archives...
python "%~dp0dm_restore.py"
echo.
pause
