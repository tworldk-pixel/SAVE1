Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

On Error Resume Next
objShell.Run "pyw """ & strDir & "\run_hidden.pyw""", 0, False
On Error Goto 0

WScript.Sleep 1800
objShell.Run "cmd /c start chrome http://localhost:8010/", 0, True
