#region --- Au3Recorder generated code Start (v3.3.9.5 KeyboardLayout=00000409)  ---

#region --- Internal functions Au3Recorder Start ---
Func _Au3RecordSetup()
Opt('WinWaitDelay',100)
Opt('WinDetectHiddenText',1)
Opt('MouseCoordMode',0)
Local $aResult = DllCall('User32.dll', 'int', 'GetKeyboardLayoutNameW', 'wstr', '')
If $aResult[1] <> '00000409' Then
  MsgBox(64, 'Warning', 'Recording has been done under a different Keyboard layout' & @CRLF & '(00000409->' & $aResult[1] & ')')
EndIf

EndFunc

Func _WinWaitActivate($title,$text,$timeout=0)
	WinWait($title,$text,$timeout)
	If Not WinActive($title,$text) Then WinActivate($title,$text)
	WinWaitActive($title,$text,$timeout)
EndFunc

_AU3RecordSetup()
#endregion --- Internal functions Au3Recorder End ---

_WinWaitActivate("Control Center - Orders 2","")
MouseClick("left",185,11,1)
MouseClick("left",221,449,1)
_WinWaitActivate("Trade Performance - Report","")
MouseClick("left",163,44,1)
MouseClick("left",111,129,1)
MouseClick("left",1142,47,1)
Sleep(750)
MouseClick("left",1169,231,1)
MouseClick("left",1256,50,1)
MouseClick("left",1274,235,1)
MouseClick("left",1293,51,1)
MouseClick("right",1340,531,1)
MouseClick("left",1382,648,1)
_WinWaitActivate("Export As","")
MouseClick("left",505,464,1)
Sleep(2500)
MouseClick("left",530,493,1)
Sleep(2500)
MouseClick("left",787,507,1)
;MouseClick("left",492,465,1)
#
;MouseClick("left",688, 679,1)
;Sleep(500)
;ControlCommand("Export As", "", "[CLASS:ComboBox; INSTANCE:2]", "SetCurrentSelection", "1" )
;Sleep(1500)
;ControlCommand( "Export As", "", "[CLASS:ComboBox; INSTANCE:2]", "SetCurrentSelection", 1)
;MouseClick("left",790,505,1)
#endregion --- Au3Recorder generated code End ---
WinWaitClose("Export As","")
Sleep(4000)
RunWait( "python .\TradePerformanceGenerator.py" )
Sleep(2000)
;$csvFiles = data\NinjaTrader\TradePerformance\*.csv
;FileDelete(C:\Trading-Test\NinjaTrader_TradesOrganizer + "$csvFiles")
RunWait("Python.exe .\ImportIntoLog.py")
;FileMove ( *trades.csv, archive\*)
;$date = @YEAR & @MON & @MDAY
;$originalFileName = "trades.csv"
;$newFileName = $date & "_" & $originalFileName
;FileMove ( $originalFileName, $newFileName)