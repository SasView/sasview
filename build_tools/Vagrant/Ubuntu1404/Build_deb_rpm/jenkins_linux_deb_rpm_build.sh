# This build script is tested for Ubuntu build VM
# This build script generates SasView Debian and RPM packages 

export PATH=$PATH:/usr/local/bin/

PYTHON=${PYTHON:-`which python`}
EASY_INSTALL=${EASY_INSTALL:-`which easy_install`}
PYLINT=${PYLINT:-`which pylint`}

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview/utils
export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview/sasview-install


cd $WORKSPACE


# SET SASVIEW GITHASH
cd $WORKSPACE
cd sasview/sasview
githash=$( git rev-parse HEAD )
sed -i.bak s/GIT_COMMIT/$githash/g __init__.py


# SASMODLES
cd $WORKSPACE
cd sasmodels

rm -rf build
rm -rf dist

$PYTHON setup.py clean
$PYTHON setup.py build


# SASMODLES - BUILD DOCS
cd  doc
make html

cd $WORKSPACE
cd sasmodels
$PYTHON setup.py bdist_egg


# SASVIEW
cd $WORKSPACE
cd sasview
rm -rf sasview-install
mkdir  sasview-install
rm -rf utils
mkdir  utils
rm -rf dist
rm -rf build


# INSTALL SASMODELS
cd $WORKSPACE
cd sasmodels
cd dist
$EASY_INSTALL -d $WORKSPACE/sasview/utils sasmodels*.egg


# BUILD SASVIEW
cd $WORKSPACE
cd sasview
$PYTHON setup.py clean
$PYTHON setup.py build docs bdist_egg


# INSTALL SASVIEW
cd $WORKSPACE
cd sasview
cd dist
$EASY_INSTALL -d $WORKSPACE/sasview/sasview-install sasview*.egg


# TEST
cd $WORKSPACE
cd sasview
cd test
$PYTHON utest_sasview.py

## PYLINT
cd $WORKSPACE
cd sasview
$PYLINT --rcfile "build_tools/pylint.rc" -f parseable sasview-install/sasview*.egg/sas sasview | tee  test/sasview.txt

# PYINSTALLER - SASVIEW
cd $WORKSPACE
cd sasview
cd sasview
pyinstaller ./sasview.spec

# CMake Debian RPM package - SASVIEW
cd $WORKSPACE
cd sasview
cd sasview
cd dist
cp $WORKSPACE/sasview/build_tools/CMakeLists.txt . 
mkdir tmp
cd tmp
cmake .. -DSAS_VERSION=4.1 -DCMAKE_INSTALL_PREFIX=/usr/local
cpack -G DEB
cpack -G RPM

# Back to WORKSPACE
cd $WORKSPACE

