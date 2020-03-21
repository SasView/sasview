# Set up path for py36 - conda
export PATH=/Users/wojciechpotrzebowski/opt/anaconda3/bin:$PATH

# List conda envs already on system
#conda env list

# Make new env from git yml file
cd $WORKSPACE
cd sasview
cd build_tools
conda env create --force -f conda_qt5_min_osx.yml
#conda env list

# Activate new env
conda_env_name="$(grep 'name: ' conda_qt5_min_osx.yml)"
echo $conda_env_name
conda_env_name=${conda_env_name:6}
echo $conda_env_name

conda activate qt5_osx

# List envs
conda list
a='/Users/wojciechpotrzebowski/opt/anaconda3/envs'
b=$conda_env_name
c='/lib'
DYLD_LIBRARY_PATH='/Users/wojciechpotrzebowski/opt/anaconda3/envs/qt5_osx/lib'
export DYLD_LIBRARY_PATH

#cd $WORKSPACE
#pip uninstall -y sasmodels

# Sasmodels
cd $WORKSPACE
cd sasmodels
python setup.py build

cd doc
make html
cd ..

python setup.py build install

# SasView
cd $WORKSPACE 
cd sasview
python src/sas/qtgui/convertUI.py
python setup.py build docs install

cd $WORKSPACE
cd sasview
cd installers
pyinstaller -y --clean --onefile --windowed sasview_qt5_osx.spec

cd dist
tar -czvf SasView.tar.gz sasview

conda deactivate

install_name_tool -change @rpath/libz.1.dylib @executable_path/../Frameworks/libz.1.dylib SasView5.0.app/Contents/MacOS/sasview

#python  ../../build_tools/code_sign_osx.py

codesign --verify --timestamp --deep --options runtime --verbose=4 --force --sign "Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)" SasView5.0.app

hdiutil create SasView5.dmg -srcfolder SasView5.0.app -ov -format UDZO

codesign -s "Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)" SasView5.dmg
