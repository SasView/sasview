@echo off
cd "c:\program files\putty"

rem Copy new installer to the temp directory on the test server
pscp -scp -v -i sasview.ppk C:\jenkins\workspace\SasView_Win7\sasview\installers\Output\setupSasView.exe sasview@192.168.1.18:AppData\Local\Temp\
rem Execute the test on the remote server
plink -i sasview.ppk -ssh sasview@192.168.1.18 c:\\jenkins\\test_deployment.bat

cd c:\jenkins
