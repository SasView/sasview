set PYTHON=c:\python27\python
set EASY_INSTALL=c:\python27\scripts\easy_install.exe
set PATH=c:\python27;c:\mingw\bin;%PATH%
set PYLINT= C:\Python27\Scripts\pylint
set INNO="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
set GIT_SED=C:\"Program Files (x86)"\Git\bin\sed.exe
set SAS_COMPILER=mingw


set PYTHONPATH=%PYTHONPATH%;%WORKSPACE%\sasview\utils
set PYTHONPATH=%PYTHONPATH%;%WORKSPACE%\sasview\sasview-install

echo %PYTHONPATH%
echo %WORKSPACE%


:: SET SASVIEW GITHASH ################################################
cd %WORKSPACE%
cd sasview\src\sas\sasview
git rev-parse HEAD > tmpFile_githash
SET /p githash= < tmpFile_githash
DEL tmpFile_githash
%GIT_SED% -i.bak "s/GIT_COMMIT/%githash%/g" __init__.py



:: MAKE DIR FOR EGGS ##################################################
cd %WORKSPACE%
cd sasview
MD sasview-install
MD utils


:: SASMODELS build ####################################################
cd %WORKSPACE%
cd sasmodels
%PYTHON% setup.py build



:: SASMODELS doc ######################################################
cd doc
make html


:: SASMODELS build egg ################################################
cd %WORKSPACE%
cd sasmodels
%PYTHON% setup.py bdist_egg
%PYTHON% -m sasmodels.model_test all

:: SASMODELS install egg ##############################################
cd %WORKSPACE%
cd sasmodels
cd dist
echo F | xcopy sasmodels-*.egg sasmodels.egg /Y
%EASY_INSTALL% -d %WORKSPACE%\sasview\utils sasmodels.egg


:: NOW BUILD SASVIEW

:: SASVIEW build egg ################################################
:: Remember to modify C:\Python27\Lib\distutils\distutils.cfg to you compiler
cd %WORKSPACE%
cd sasview
%PYTHON% setup.py build docs bdist_egg


:: SASVIEW utest ######################################################
cd %WORKSPACE%\sasview\test
%PYTHON% utest_sasview.py


:: SASVIEW INSTALL EGG ################################################
cd %WORKSPACE%
cd sasview
cd dist
echo F | xcopy sasview-*.egg sasview.egg /Y
%EASY_INSTALL% -d %WORKSPACE%\sasview\sasview-install sasview.egg


:: TINYCC build ####################################################
cd %WORKSPACE%
cd tinycc
%PYTHON% setup.py build
xcopy /S build\lib\* %WORKSPACE%\sasview\utils\

:: SASVIEW INSTALLER ##################################################
cd %WORKSPACE%
cd sasview
cd installers
%PYTHON% setup_exe.py py2exe
%PYTHON% installer_generator.py
%INNO% installer.iss
cd Output
xcopy setupSasView.exe %WORKSPACE%\sasview\dist

:: SASVIEW PYLINT #####################################################
cd %WORKSPACE%\sasview
%PYLINT% --rcfile "build_tools/pylint.rc" -f parseable sasview-install/sasview.egg/sas sasview > test/sasview.txt


:: GO BACK ############################################################
cd %WORKSPACE%
