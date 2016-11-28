How to setup VM SasViewQt Ubuntu1404 developer env using Vagrant

A: Provision VM

B: Log on to VM - Setup Anaconda
01) Install miniconda: $ bash ./Miniconda2-latest-Linux-x86_64.sh
02) Export miniconda path: $ export PATH=/home/vagrant/miniconda2/bin:$PATH 
03) Make sasviewqt env in minicona: conda env create -f environment.yml

C: Build SasView
04) clone sasview: git clone https://github.com/SasView/sasview
05) clone sasmodels: git clone https://github.com/SasView/sasmodels
06) show sasview branch: git remote show origin
07) checkout ESS_GUI: git checkout ESS_GUI
08) build sasmodels: python setup.py build
09) build sasmodels doc: make html
10) build sasview: python setup.py build
11) build sasview: python setup.py docs
12) run sasview: python run.py
12) cd SasView/sasview/src/sas/qtgui
13) make gui: ./make_ui.sh
14) python run.py / python Main_Window.py depending on on your cloned githash

Tips:
export PATH=/home/vagrant/miniconda2/bin:$PATH

conda env export > environment.yml
conda env create -f environment.yml


# To activate this environment, use:
# > source activate sasviewqt
#
# To deactivate this environment, use:
# > source deactivate sasviewqt



Known problems:
libxml2 not installed.


