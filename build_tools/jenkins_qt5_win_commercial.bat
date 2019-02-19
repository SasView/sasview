:: Find ENV NAME
cd %WORKSPACE%
cd sasview
cd build_tools
findstr "name:" conda_qt5_win.yml > condaenv_name.txt
set /p condaname=<condaenv_name.txt

:: ACTIVATE ENV
call activate %condaname:~6%


:: BUILD SETUP
set PYTHON=python.exe
set EASY_INSTALL=easy_install.exe
set PYLINT= pylint.exe
set PYINSTALLER=pyinstaller.exe
set INNO=C:\"Program Files (x86)"\"Inno Setup 5"\ISCC.exe
set GIT_SED=C:\"Program Files"\Git\bin\sed.exe
set SAS_COMPILER=tinycc


:: REMOVE INSTALLATION ################################################
pip uninstall -y sasview
pip uninstall -y sasmodels
pip uninstall -y tinycc

:: TINYCC build ####################################################
cd %WORKSPACE%
cd tinycc
%PYTHON% setup.py build install

:: SASMODELS build ####################################################
cd %WORKSPACE%
cd sasmodels
%PYTHON% setup.py build

:: SASMODELS doc ######################################################
cd doc
make html

:: SASMODELS install ################################################
cd %WORKSPACE%
cd sasmodels
%PYTHON% setup.py install


:: NOW BUILD SASVIEW

:: SASVIEW check dep ################################################
cd %WORKSPACE%
cd sasview
%PYTHON% check_packages.py


:: SASVIEW build install ################################################
cd %WORKSPACE%
cd sasview

:: MAKE GUI FROM UI FILES
%PYTHON% src\sas\qtgui\convertUI.py
%PYTHON% setup.py build docs install


:: :: SASVIEW utest ######################################################
:: NOT YET IMPLEMENTED FOR THE NEW Qt5 SasView 5.0 
:: cd %WORKSPACE%\sasview\test
:: %PYTHON% utest_sasview.py


:: SASVIEW INSTALLER ##################################################
cd %WORKSPACE%
cd sasview
cd installers

:: USING PYINSTALLER
%PYINSTALLER% sasview_qt5_commercial.spec

::# :: USING PY2EXE
::# %PYTHON% setup_exe.py py2exe


:: READY FOR INNO
%PYTHON% installer_generator64.py
%INNO% installer.iss
cd Output
xcopy setupSasView.exe %WORKSPACE%\sasview\dist
