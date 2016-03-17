
set PYTHON=C:\Python27\python
set EASY_INSTALL=c:\python27\scripts\easy_install.exe
set NEXUSDIR="C:\Program Files (x86)\NeXus Data Format\"
set PATH=C:\Python27;C:\Python27\Scripts;C:\mingw\bin;%PATH%
set PYLINT=c:\python27\scripts\pylint


cd %WORKSPACE%
%PYTHON% check_packages.py


cd %WORKSPACE%
python setup.py build -cmingw32


cd %WORKSPACE%
python setup.py docs


cd %WORKSPACE%
python setup.py bdist_egg --skip-build


cd %WORKSPACE%\test
%PYTHON% utest_sasview.py


cd %WORKSPACE%
mkdir sasview-install
set PYTHONPATH=%WORKSPACE%\sasview-install;%PYTHONPATH%


cd %WORKSPACE%
cd dist
%EASY_INSTALL% -d ..\sasview-install sasview-3.1.2-py2.7-win32.egg


cd %WORKSPACE%\sasview
python setup_exe.py py2exe
python installer_generator.py
"C:\Program Files (x86)\Inno Setup 5\ISCC.exe" installer.iss 


cd Output
xcopy setupSasView.exe %WORKSPACE%\dist

cd %WORKSPACE%
%PYLINT% --rcfile "%WORKSPACE%cd /build_tools/pylint.rc" -f parseable sasview-install/sasview*.egg/sas sasview > test/sasview.txt


cd  %WORKSPACE%
