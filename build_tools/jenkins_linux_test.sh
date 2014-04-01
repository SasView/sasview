#! /bin/sh

# try to find reasonable settings, if not provided in the environment
PYTHON=${PYTHON:-`which python`}
PYLINT=${PYLINT:-`which pylint`}
BUILD_TOOLS_DIR=`dirname $0`
WORKSPACE=${WORKSPACE:-`readlink -f $BUILD_TOOLS_DIR/..`}
# WORKSPACE top level of source

cd $WORKSPACE/test

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview-install:$WORKSPACE/utils

$PYTHON utest_sansview.py
