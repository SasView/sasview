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

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview-install:$WORKSPACE/utils

$PYTHON setup.py bdist_egg

cd $WORKSPACE/dist
EASY_INSTALL -N -d ../sasview-install sasview*.egg
