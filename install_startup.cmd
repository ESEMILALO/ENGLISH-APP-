@echo off
setlocal
cd /d "%~dp0"

REM  Makes Word Log start on its own when you log in, so the app on your
REM  phone always has something to talk to. No administrator rights
REM  needed -- this only adds a shortcut to your own Startup folder.
REM
REM  To undo it, run this again and choose R, or just delete the shortcut
REM  from the folder that opens with:  explorer shell:startup

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LINK=%STARTUP%\Word Log.lnk"

if /i "%~1"=="remove" goto remove
if exist "%LINK%" (
  echo.
  echo   Word Log already starts at login.
  echo.
  set /p ANS="  Press R to remove it, or any other key to leave it: "
  if /i "%ANS%"=="R" goto remove
  echo   Left as it is.
  goto done
)

powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LINK%');" ^
  "$s.TargetPath='wscript.exe';" ^
  "$s.Arguments='\"%~dp0run_hidden.vbs\"';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.IconLocation='%SystemRoot%\system32\shell32.dll,14';" ^
  "$s.Description='Serves Word Log to your own devices over Tailscale';" ^
  "$s.Save()"

if exist "%LINK%" (
  echo.
  echo   Done. Word Log will start quietly every time you log in.
  echo.
) else (
  echo.
  echo   Could not create the shortcut. You can add it by hand: press
  echo   Win+R, type  shell:startup  and drop run_hidden.vbs in there.
  echo.
)
goto done

:remove
if exist "%LINK%" del "%LINK%"
echo.
echo   Removed. Word Log will no longer start by itself.
echo   Double-click start_word_log.cmd when you want it.
echo.

:done
pause
