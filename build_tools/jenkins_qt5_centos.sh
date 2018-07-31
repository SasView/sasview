# Activate new env
cd $WORKSPACE
cd sasview
cd build_tools

conda_env_name="$(grep 'name: ' conda_qt5_min_centos.yml)"
echo $conda_env_name
conda_env_name=${conda_env_name:6}
echo $conda_env_name

source activate $conda_env_name


# Now build Sasview

# Sasmodels
cd $WORKSPACE
cd sasmodels
python setup.py build

cd $WORKSPACE
cd sasmodels
cd doc
make html

cd $WORKSPACE
cd sasmodels
python setup.py build install


# SasView
cd $WORKSPACE 
cd sasview
python src/sas/qtgui/convertUI.py
python setup.py build docs
python setup.py install

# Pyinstaller
cd $WORKSPACE 
cd sasview
cd installers
pyinstaller sasview_qt5_min_centos.spec

cd $WORKSPACE 
cd sasview
cd installers
cp run_sasview.sh dist/sasview
cp set_sasview_qt5_path.sh dist/sasview
cd dist
mv sasview SasView
tar czvf SasView.tar.gz SasView

