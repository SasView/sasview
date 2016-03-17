#! /bin/sh
set -x

# try to find reasonable settings, if not provided in the environment
PYTHON=${PYTHON:-`which python`}
PYLINT=${PYLINT:-`which pylint`}
#BUILD_TOOLS_DIR=`dirname $0`
#WORKSPACE=${WORKSPACE:-`readlink -f $BUILD_TOOLS_DIR/..`}
# WORKSPACE top level of source




export PYTHONPATH=$WORKSPACE/sasview/sasview-install:$WORKSPACE/sasview/utils:$PYTHONPATH

cd $WORKSPACE/sasview
rm -f test/sasview.txt

$PYLINT --rcfile "build_tools/pylint.rc" -f parseable sasview-install/sasview*.egg/sas sasview > test/sasview.txt
