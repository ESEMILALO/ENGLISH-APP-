' Starts Word Log with no console window.
' Used by the Startup shortcut; double-click start_word_log.cmd instead
' when you want to see what it is doing.
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = here
shell.Run """" & here & "\start_word_log.cmd""", 0, False
