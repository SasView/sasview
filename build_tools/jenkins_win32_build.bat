cd %WORKSPACE%
set PYTHON=c:\python26\python
set EASY_INSTALL=c:\python26\scripts\easy_install.exe
set NEXUSDIR="C:\Program Files (x86)\NeXus Data Format\"
set PATH=c:\python26;c:\mingw\bin;%PATH%

echo %SVN_REVISION%> svn_revision.txt

%PYTHON% check_packages.py

set PYTHONPATH=%WORKSPACE%\sansview-install;%PYTHONPATH%

RD /S /Q sansview-install
MD sansview-install
RD /S /Q dist
RD /S /Q build

rem %PYTHON% -m pip install -t ../sansview-install --no-deps bumps=0.7.5.2
rem PYTHON% -m pip install -t ../sansview-install --no-deps periodictable=1.3.0
rem %PYTHON% -m pip install -t ../sansview-install --no-deps pyparsing=1.5.5

%PYTHON% setup.py build -cmingw32
%PYTHON% setup.py bdist_egg --skip-build
cd dist
%EASY_INSTALL% -d ..\sansview-install sasview*.egg

cd %WORKSPACE%\test
%PYTHON% utest_sansview.py