
set PYTHON=c:\Python27\python
set EASY_INSTALL=c:\python27\scripts\easy_install.exe
set PATH=c:\python27;c:\mingw\bin;%PATH%
set PYLINT=c:\python27\scripts\pylint

set PYTHONPATH=%WORKSPACE%\sasview-install;%PYTHONPATH%



cd %WORKSPACE%

del /F test\sasview.txt

%PYLINT% --rcfile "%WORKSPACE%/build_tools/pylint.rc" -f parseable sasview-install/sasview*.egg/sas sasview > test/sasview.txt

cd %WORKSPACE%