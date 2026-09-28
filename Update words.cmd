@echo off
setlocal
cd /d "%~dp0"

REM  Rebuilds the app from the spreadsheet.
REM
REM  Edit "ENGLISH SCHOOL.xlsx", save it, then double-click this. Refresh
REM  Word Log afterwards and the new words are there.

echo.
echo   Rebuilding Word Log from ENGLISH SCHOOL.xlsx
echo.

python tools\build_word_log.py

echo.
pause
