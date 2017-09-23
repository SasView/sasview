export PATH=$PATH:/usr/local/bin/

PYTHON=${PYTHON:-`which python`}
EASY_INSTALL=${EASY_INSTALL:-`which easy_install`}
PYLINT=${PYLINT:-`which pylint`}

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview/utils
export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview/sasview-install
export PYTHONPATH=$PYTHONPATH:/Library/Python/2.7/site-packages

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8


cd $WORKSPACE

# SET SASVIEW GITHASH
cd $WORKSPACE
cd sasview/src/sas/sasview
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

#SASMODELS - BUILDING AND TESTING
cd $WORKSPACE
cd sasmodels
$PYTHON setup.py bdist_egg
$PYTHON -m sasmodels.model_test all

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

# PYLINT
cd $WORKSPACE
cd sasview
$PYLINT --rcfile "build_tools/pylint.rc" -f parseable sasview-install/sasview*.egg/sas sasview | tee  test/sasview.txt

# BUILD APP
cd $WORKSPACE
cd sasview/installers
$PYTHON setup_mac.py py2app

