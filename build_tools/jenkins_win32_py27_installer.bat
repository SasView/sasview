cd %WORKSPACE%

set EASY_INSTALL=c:\python27\scripts\easy_install.exe
set PYTHONPATH=%WORKSPACE%\sasview-install

python setup.py build -cmingw32
python setup.py docs
python setup.py bdist_egg --skip-build

RD /S /Q sasview-install
MD sasview-install

REM cd dist
REM %EASY_INSTALL% -d ..\sasview-install sasview-3.0.0_r0-py2.7-win32.egg

cd %WORKSPACE%\sasview
python setup_exe.py py2exe
python installer_generator.py
"C:\Program Files (x86)\Inno Setup 5\ISCC.exe" installer.iss

cd Output
xcopy setupSasView.exe %WORKSPACE%\dist