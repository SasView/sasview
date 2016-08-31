; ****** REMEMBER TO SWITCH OFF UAC ON TARGET MACHINE!!! *********
;
; This script will install, run and uninstall SasView
; given location of the installer. The exit code of the script
; points at failure location:
;
; 0 - OK
; 1 - Installer failure
; 2 - Problems running SasView (simple fitting)
; 3 - Uninstaller failure

#include <Constants.au3>
#include <FileConstants.au3>
#include <MsgBoxConstants.au3>
#include <WinAPIFiles.au3>

; Modifiable globals
Global $fInstallerLocation = @TempDir & "\setupSasView.exe"
if $CmdLine[0] > 0 Then
   ; If argument present - use it as local download path
   $fInstallerLocation = $CmdLine[1]
EndIf

Global $fUninstallerLocation = "C:\Program Files (x86)\SasView\unins000.exe"
Global $lTimeout = 10          ; 10 sec timeout for waiting on windows
Global $lInstallTimeout = 120  ; 2 min timeout for the installation process

; General globals
Global $installerPID = 0

;; MAIN SCRIPT
Install()
RunSasView()
Uninstall()
Exit(0)

;==============================================================

Func Install()
   ;;;;; APPLICATION INSTALLED ;;;;;;;
   Local $sSetupWindow = "Setup - SasView"
   Local $iFailFlag = 1
   ; Run setup
   if FileExists($fInstallerLocation) Then
	  $installerPID = Run($fInstallerLocation)
	  Assert($installerPID, $iFailFlag)
	  Sleep(1000)
   Else
	  ;$Error = ObjEvent(AutoIt.Error, "Setup file does not exist","123")
	  Exit($iFailFlag)
   EndIf

   ; License click through
   WinActivate($sSetupWindow)
   Local $test = WinWaitActive($sSetupWindow, "License Agreement", $lTimeout)
   ;ConsoleWrite("license agreement: " & $test)
   Assert($test, $iFailFlag)
   sleep(1000)

   Send("{TAB}{up}{ENTER}")

   ; Location
   Sleep(1000)
   $test = WinWaitActive($sSetupWindow, "Select Destination Location", $lTimeout)
   Assert($test, $iFailFlag)
   Send("{ENTER}")

   ; Icons, Startup entry
   Sleep(1000)
   $test = WinWaitActive($sSetupWindow, "Select Additional Tasks", $lTimeout)
   Assert($test, $iFailFlag)
   Send("{ENTER}")

   ; Ready to install...
   Sleep(1000)
   $test = WinWaitActive($sSetupWindow, "Ready to Install", $lTimeout)
   Assert($test, $iFailFlag)
   Send("{ENTER}")

   ; Final OK on running
   Sleep(5000)
   $test = WinWaitActive($sSetupWindow, "Completing the SasView Setup Wizard", $lInstallTimeout)
   Assert($test, $iFailFlag)
   Send("{ENTER}")
   ;ConsoleWrite("Installed" & @CRLF)

EndFunc


Func RunSasView()
   ;;;;; APPLICATION STARTED ;;;;;;;
   ; Start app - DEBUG ONLY
   ;;Run("C:\Program Files (x86)\SasView\SasView.exe")
   local $sActiveWindow = "SasView  - Fitting -"
   Local $iFailFlag = 2
   ; Wait for the window
   Sleep(1000)
   Local $hWnd = WinWaitActive($sActiveWindow, "", $lTimeout)
   Assert($hWnd, $iFailFlag)

   ;;;;; Load a File
   ; Open File Load dialog
   Send("!{f}{ENTER}")
   WinWaitActive("Choose a file", "", $lTimeout)
   Assert($hWnd, $iFailFlag)
   Sleep(200)

   ; Focus is in file chooser - enter filename
   Send("C:\Program Files (x86)\SasView\test\1d_data\cyl_400_20.txt")
   Sleep(1000)
   Send("{ENTER}")

   ;; Send file to fitting
   ControlClick($hWnd, "Send To", 231)

   ;; Choose a python model
   ControlCommand($hWnd, "", "ComboBox3", "SetCurrentSelection", 1)
   ;; Calculate the model
   ControlClick($hWnd, "Compute", 211)
   ;; Assure we got the charts
   Local $hPlot = WinWait($sActiveWindow, "Graph2", $lTimeout)
   Assert($hPlot, $iFailFlag)
   $hPlot = WinWait($sActiveWindow, "Graph3", $lTimeout)
   Assert($hPlot, $iFailFlag)

   sleep(1000)
   ;; Calculate a compiled model
   ControlClick($hWnd, "Send To", 231)

   ;; Choose Shapes/Cylinder
   ControlCommand($hWnd, "", "ComboBox2", "SetCurrentSelection", 1)
   ControlCommand($hWnd, "", "ComboBox3", "SetCurrentSelection", 11)
   ;; Calculate the model
   ControlClick($hWnd, "Compute", 211)

   ;; Assure we got another chart
   $hPlot = WinWait($sActiveWindow, "Graph4", $lTimeout)
   Assert($hPlot, $iFailFlag)

   ;; Close SasView
   WinClose($hWnd)

   Local $hEnd = WinWaitActive("Confirm Exit", "", $lTimeout)
   Assert($hEnd, $iFailFlag)
   ControlClick($hEnd, "", "[CLASS:Button; INSTANCE:1]")

   Local $sv_closed = WinWaitClose($hWnd, "", $lTimeout)
   Assert($sv_closed, $iFailFlag)

EndFunc

Func Uninstall()
;;;;; UNINSTALL ;;;;;;;
   Local $iFailFlag = 3
   $installerPID = Run($fUninstallerLocation)
   Assert($installerPID, $iFailFlag)

   Local $sSetupWindow = "SasView Uninstall"

   Local $test = WinWaitActive($sSetupWindow, "", $lTimeout)
   Assert($test, $iFailFlag)
   Send("{TAB}{ENTER}")

   WinActivate("SasView Uninstal")
   $test = WinWaitActive($sSetupWindow, "SasView was successfully removed", $lTimeout)
   Assert($test, $iFailFlag)
   Send("{ENTER}")

EndFunc


;;; HELPER FUNCTIONS ;;;;
Func Assert($test, $lExitValue)
   ;;; Asserts $test to be non-zero and exit with code $lExitValue ;;;
   if $test == 0 Then
	  ProcessClose($installerPID)
	  Exit($lExitValue)
   EndIf
EndFunc
