@echo off
cd c:\jenkins

rem sasview.exe is an AutoIt3 generated binary based on sasview_deploy_test.au3
start /wait c:\jenkins\sasview.exe %1 %2

echo %errorlevel%

