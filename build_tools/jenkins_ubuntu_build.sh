# Set up correct shell
#!/bin/bash

## Set up path for py36 - conda
export PATH=/home/sasview/anaconda3/bin:$PATH
export QT_QPA_PLATFORM=offscreen

# Set proxy
export http_proxy=http://192.168.1.1:8123
export https_proxy=http://192.168.1.1:8123

# List conda envs already on system
conda env list

# Make new env from git yml file
cd $WORKSPACE
cd sasview
cd build_tools
conda env create --force -f conda_qt5_min_ubuntu.yml
# conda env create --force -f conda_qt5_ubuntu.yml
conda env list

# Activate new env
source activate qt5_ubuntu
conda list
conda env list

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
python setup.py build docs install

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

