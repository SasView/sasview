#! /bin/sh

# try to find reasonable settings, if not provided in the environment
PYTHON=${PYTHON:-`which python`}
EASY_INSTALL=${EASY_INSTALL:-`which easy_install`}
PYLINT=${PYLINT:-`which pylint`}
#BUILD_TOOLS_DIR=`dirname $0`
#WORKSPACE=${WORKSPACE:-`readlink -f $BUILD_TOOLS_DIR/..`}
# WORKSPACE top top level of source  


cd $WORKSPACE

cd $WORKSPACE/sasview

if [ ! -d "utils" ]; then
    mkdir utils
fi

rm -rf sasview-install
mkdir sasview-install
rm -rf dist
rm -rf build


export PYTHONPATH=$WORKSPACE/sasview/sasview-install:$WORKSPACE/sasview/utils:$PYTHONPATH


"$EASY_INSTALL" -d "$WORKSPACE/sasview/utils" bumps==0.7.5.6
"$EASY_INSTALL" -d "$WORKSPACE/sasview/utils" periodictable==1.3.0

# CHECK_PACKAGES
$PYTHON check_packages.py

# BUILD_CODE
$PYTHON setup.py build

# TEST_CODE
cd test
$PYTHON utest_sasview.py
cd ..

# BUILD_DOCS
$PYTHON setup.py docs

# BUILD_EGG 
$PYTHON setup.py bdist_egg --skip-build

#cd $WORKSPACE/sasview/dist
##ln -s sasview*.egg sasview.egg || true
#$EASY_INSTALL -N -d ../sasview-install sasview*.egg

cd $WORKSPACE

