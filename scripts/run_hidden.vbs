Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
baseDir = fso.GetParentFolderName(scriptDir)

If shell.Run("cmd /c where py >nul 2>nul", 0, True) = 0 Then
    pythonLauncher = "py -3"
Else
    pythonLauncher = "python"
End If

command = "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command ""Set-Location -LiteralPath '" & baseDir & "'; " & pythonLauncher & " '" & baseDir & "\scripts\monitor_agent.py'"""

shell.Run command, 0, False
