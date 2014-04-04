#! /bin/sh

# try to find reasonable settings, if not provided in the environment
PYTHON=${PYTHON:-`which python`}
PYLINT=${PYLINT:-`which pylint`}
BUILD_TOOLS_DIR=`dirname $0`
WORKSPACE=${WORKSPACE:-`readlink -f $BUILD_TOOLS_DIR/..`}
# WORKSPACE top level of source


cd $WORKSPACE/sasview-install
export SASVIEWMODULE=`echo sasview-*`
ln -s $SASVIEWMODULE forpylint.egg

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview-install:$WORKSPACE/utils

cd $WORKSPACE
rm -f test/*.txt

$PYLINT --rcfile $WORKSPACE/build_tools/pylint.rc -f parseable sasview-install/forpylint.egg/sans sansview > test/sansview.txt || true

exit 0
