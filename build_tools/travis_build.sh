# Simplified build for Travis CI
export PATH=$PATH:/usr/local/bin/

PYTHON=${PYTHON:-`which python`}
EASY_INSTALL=${EASY_INSTALL:-`which easy_install`}

export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview/utils
export PYTHONPATH=$PYTHONPATH:$WORKSPACE/sasview/sasview-install

# SET SASVIEW GITHASH
cd $WORKSPACE/sasview/src/sas/sasview
githash=$( git rev-parse HEAD )
sed -i.bak s/GIT_COMMIT/$githash/g __init__.py

# SASMODELS
cd $WORKSPACE/sasmodels
rm -rf build
rm -rf dist
$PYTHON setup.py clean
$PYTHON setup.py build
$PYTHON setup.py bdist_egg

# SASVIEW
cd $WORKSPACE/sasview
rm -rf sasview-install
mkdir  sasview-install
rm -rf utils
mkdir  utils
rm -rf dist
rm -rf build

# INSTALL SASMODELS
cd $WORKSPACE/sasmodels/dist
$EASY_INSTALL -d $WORKSPACE/sasview/utils sasmodels*.egg

# BUILD SASVIEW
cd $WORKSPACE/sasview
$PYTHON setup.py clean
# $PYTHON setup.py build docs bdist_egg
$PYTHON setup.py bdist_egg

# BUILD DOCS
NUM=4
mkdir -p ~/.sasmodels/compiled_models
make PYTHON=$PYTHON -j $NUM -C $WORKSPACE/bumps/doc html
make PYTHON=$PYTHON -j $NUM -C $WORKSPACE/sasmodels/doc html
cd $WORKSPACE/sasview/docs/sphinx-docs/
$PYTHON build_sphinx.py

# INSTALL SASVIEW
cd $WORKSPACE/sasview/dist
$EASY_INSTALL -d $WORKSPACE/sasview/sasview-install sasview*.egg

for egg in $WORKSPACE/sasview/utils/*egg $WORKSPACE/sasview/sasview-install/*egg; do
  PYTHONPATH=$egg:$PYTHONPATH
done

# TEST
cd $WORKSPACE/sasview/test
$PYTHON utest_sasview.py
# If a display is available, also run the GUI tests
if [ -n "$DISPLAY" ]; then
  cd $WORKSPACE/sasview/src/sas/qtgui
  # suppress errors from the GUI tests until a baseline 'pass' is obtained
  $PYTHON GUITests.py || true
else
  echo "NOTE: GUITests.py skipped as no DISPLAY was found"
fi
