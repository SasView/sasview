#!/bin/sh

# Check envorionment variables set by Jenkins #############################
if [ -z "$WORKSPACE" ]; then
	WORKSPACE=`pwd`
fi

if [ -z "$SVN_REVISION" ]; then
	SVN_REVISION=''
fi

export SASVIEW_INSTALL=sasview-install

if [ -z "$EASY_INSTALL" ]; then
	EASY_INSTALL=`which easy_install`
fi


# Set up build environmentRun tests #######################################
cd $WORKSPACE

#  Check dependencies
if [ ! -d "utils" ]; then
    mkdir utils
fi
export PYTHONPATH=$PYTHONPATH:$WORKSPACE/utils
"$EASY_INSTALL" -d "$WORKSPACE/utils" unittest-xml-reporting
"$EASY_INSTALL" -d "$WORKSPACE/utils" lxml
"$EASY_INSTALL" -d "$WORKSPACE/utils" pyparsing==1.5.5
"$EASY_INSTALL" -d "$WORKSPACE/utils" bumps==0.7.5.9
"$EASY_INSTALL" -d "$WORKSPACE/utils" periodictable==1.5.0
python deps.py

#  Set up working directories
rm -rf $SASVIEW_INSTALL
mkdir $SASVIEW_INSTALL

rm -rf $WORKSPACE/dist
mkdir $WORKSPACE/dist

rm -rf build


# Build SasView ###########################################################
export PYTHONPATH=$PYTHONPATH:$WORKSPACE/$SASVIEW_INSTALL:$WORKSPACE/utils
python setup.py bdist_egg


# Run tests ###############################################################
#  Install it locally so we can test it
cd $WORKSPACE/dist
easy_install -d ../$SASVIEW_INSTALL sasview*.egg

#  Run tests
cd $WORKSPACE/test
python utest_sasview.py


# Build RPM ###############################################################
cd ${HOME}/rpmbuild/SOURCES
rm -rf *.egg
cp $WORKSPACE/dist/*.egg .

rm -rf $WORKSPACE/dist/*.rpm

cd ${WORKSPACE}/build_tools/rpm
python create_rpm_spec.py ${SVN_REVISION}
cp sasview.spec ${HOME}/rpmbuild/SPECS

cd ${HOME}/rpmbuild/SPECS
rpmbuild -bb sasview.spec --clean
cp ${HOME}/rpmbuild/RPMS/x86_64/* ${WORKSPACE}/dist

