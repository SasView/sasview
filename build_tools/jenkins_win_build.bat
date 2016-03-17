
set PYTHON=C:\Python27\python
set EASY_INSTALL=c:\python27\scripts\easy_install.exe
set NEXUSDIR="C:\Program Files (x86)\NeXus Data Format\"
set PATH=C:\Python27;C:\Python27\Scripts;C:\mingw\bin;%PATH%
set PYLINT=c:\python27cscripts\pylint


cd %WORKSPACE%\sasview
%PYTHON% check_packages.py


cd %WORKSPACE%\sasview
python setup.py build -cmingw32


cd %WORKSPACE%\sasview
python setup.py docs


cd %WORKSPACE%\sasview
python setup.py bdist_egg --skip-build


cd %WORKSPACE%\sasview\test
%PYTHON% utest_sasview.py


cd %WORKSPACE%\sasview
mkdir sasview-install
set PYTHONPATH=%WORKSPACE%\sasview\sasview-install;%PYTHONPATH%


cd %WORKSPACE%\sasview
cd dist
%EASY_INSTALL% -d ..\sasview-install sasview-3.1.2-py2.7-win32.egg


cd %WORKSPACE%\sasview\sasview
python setup_exe.py py2exe
python installer_generator.py
"C:\Program Files (x86)\Inno Setup 5\ISCC.exe" installer.iss 


cd Output
xcopy setupSasView.exe %WORKSPACE%\sasview\dist

cd %WORKSPACE%\sasview
%PYLINT% --rcfile "build_tools/pylint.rc" -f parseable sasview-install/sasview*.egg/sas sasview > test/sasview.txt


cd  %WORKSPACE%
