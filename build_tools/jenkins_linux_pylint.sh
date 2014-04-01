#! /bin/sh

# try to find reasonable settings, if not provided in the environment
PYTHON=${PYTHON:-`which python`}
PYLINT=${PYLINT:-`which pylint`}
BUILD_TOOLS_DIR=`dirname $0`
WORKSPACE=${WORKSPACE:-`readlink -f $BUILD_TOOLS_DIR/..`}
# WORKSPACE top level of source


cd $WORKSPACE/sasview-install
export SASVIEWMODULE=`echo sasview-*`

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview-install:$WORKSPACE/utils

cd $WORKSPACE
rm -f test/*.txt

$PYLINT --rcfile $WORKSPACE/build_tools/pylint.rc -f parseable sasview-install/$SASVIEWMODULE/sans sansview > test/sansview.txt || exit 0
