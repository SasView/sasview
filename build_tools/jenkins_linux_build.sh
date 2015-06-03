#! /bin/sh

# try to find reasonable settings, if not provided in the environment
PYTHON=${PYTHON:-`which python`}
EASY_INSTALL=${EASY_INSTALL:-`which easy_install`}
PYLINT=${PYLINT:-`which pylint`}
BUILD_TOOLS_DIR=`dirname $0`
WORKSPACE=${WORKSPACE:-`readlink -f $BUILD_TOOLS_DIR/..`}
# WORKSPACE top level of source

cd $WORKSPACE
rm -rf sasview-install
mkdir sasview-install
rm -rf dist
rm -rf build

"$EASY_INSTALL" -d "$WORKSPACE/utils" bumps==0.7.5.6
"$EASY_INSTALL" -d "$WORKSPACE/utils" periodictable==1.3.0

export PYTHONPATH=$WORKSPACE/sasview-install:$WORKSPACE/utils:$PYTHONPATH

$PYTHON check_packages.py
$PYTHON setup.py bdist_egg

cd $WORKSPACE/dist
# ln -s sasview*.egg sasview.egg || true
$EASY_INSTALL -N -d ../sasview-install sasview*.egg

