export PATH=$PATH:/usr/local/bin/

cd $WORKSPACE

export PYTHONPATH=$WORKSPACE/sasview-install:$WORKSPACE/utils:$PYTHONPATH

##########################################################################
# Use git/svn scripts

#  Check dependencies
cd $WORKSPACE
if [ ! -d "utils" ]; then
    mkdir utils
fi


# BUILD_CODE
cd $WORKSPACE
/bin/sh -xe build_tools/jenkins_linux_build.sh


# TEST_CODE
cd $WORKSPACE
/bin/sh -xe build_tools/jenkins_linux_test.sh


# BUILD DOCS
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
cd $WORKSPACE
python setup.py docs


# BUILD_egg with new docs
cd $WORKSPACE
python setup.py bdist_egg --skip-build


# PYLINT_CODE
#cd $WORKSPACE
#/bin/sh -xe build_tools/jenkins_linux_pylint.sh


# BUILD APP
cd $WORKSPACE/sasview
python setup_mac.py py2app

cd $WORKSPACE/sasview/dist
tar -czf `python -c "import pkg_resources;print '%s.tar.gz' % pkg_resources.get_distribution('sasview').egg_name()"` sasview.app
