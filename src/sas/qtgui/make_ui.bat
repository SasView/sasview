@echo off

cd UI
call convert_rc.bat main_resources
call convert_all.bat

cd ..\images
call convert_rc.bat images
cd ..


cd Perspectives
cd Fitting\UI
call convert_all.bat
cd ..\..\Invariant\UI
call convert_all.bat

cd ..\..\..

