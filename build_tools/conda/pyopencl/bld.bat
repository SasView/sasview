xcopy %RECIPE_DIR%\bin %PREFIX%\DLLs /E
xcopy %RECIPE_DIR%\include %PREFIX%\include /E
xcopy %RECIPE_DIR%\lib %PREFIX%\libs /E

xcopy %RECIPE_DIR%\bin %PREFIX%\Library\bin /E
xcopy %RECIPE_DIR%\include %PREFIX%\Library\include /E
xcopy %RECIPE_DIR%\lib %PREFIX%\Library\lib /E

::"%PYTHON%" setup.py build -cmingw32
"%PYTHON%" configure.py
if errorlevel 1 exit 1
"%PYTHON%" setup.py build
if errorlevel 1 exit 1
"%PYTHON%" setup.py install
if errorlevel 1 exit 1

:: Add more build steps here, if they are necessary.

:: See
:: http://docs.continuum.io/conda/build.html
:: for a list of environment variables that are set during the build process.
