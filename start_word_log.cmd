@echo off
setlocal
cd /d "%~dp0"

REM  Starts Word Log and puts it on your tailnet over https.
REM
REM  Double-click this, or let it run at login (see install_startup.cmd).
REM  Everything it does is private to your own devices: the server itself
REM  listens on 127.0.0.1 only, and Tailscale answers nobody who is not
REM  signed in to your tailnet.

set TS="C:\Program Files\Tailscale\tailscale.exe"
set PORT=8777
set HTTPS_PORT=8443

echo.
echo   Word Log
echo   --------
echo.

REM  Put Tailscale in front of the local server. --bg keeps the mapping
REM  after this window closes; running it again just re-states the same
REM  thing, so it is safe to run at every login.
%TS% serve --bg --https=%HTTPS_PORT% http://127.0.0.1:%PORT% >nul 2>&1

REM  The server prints the address to open -- it asks Tailscale for this
REM  machine's name rather than having it written down here.
python -u serve_word_log.py --port %PORT% --https-port %HTTPS_PORT%
