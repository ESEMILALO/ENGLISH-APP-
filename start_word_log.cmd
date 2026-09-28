@echo off
setlocal
cd /d "%~dp0"

REM  Starts Word Log on this laptop.
REM
REM  Double-click this, or let it run at login (see install_startup.cmd).
REM  The server binds to this machine's loopback address only, so the app
REM  is not reachable from the wifi, from the internet, or from any other
REM  device. That is the socket itself, not a setting.

python -u serve_word_log.py
