Ubuntu Vagrant Setup for SasViewQt 
----------------------------------

How-to setup VM SasViewQt Ubuntu1404 developer env using Vagrant

A: Provision VM
---------------

B: Log on to VM - Setup Anaconda
--------------------------------

1. Install miniconda: $ bash ./Miniconda2-latest-Linux-x86_64.sh
2. Export miniconda path: $ export PATH=/home/vagrant/miniconda2/bin:$PATH 
3. Make sasviewqt env in minicona: conda env create -f environment.yml

C: Build SasView
----------------
1. clone sasview: git clone https://github.com/SasView/sasview
2. clone sasmodels: git clone https://github.com/SasView/sasmodels
3. show sasview branch: git remote show origin
4. checkout ESS\_GUI: git checkout ESS\_GUI
5. build sasmodels: python setup.py build
6. build sasmodels doc: make html
7. build sasview: python setup.py build
8. build sasview: python setup.py docs
9. run sasview: python run.py
10. cd SasView/sasview/src/sas/qtgui
11. make gui: ./make_ui.sh
12.python run.py / python Main\_Window.py depending on on your cloned githash

Tips:
----

   - $ export PATH=/home/vagrant/miniconda2/bin:$PATH
   - $ conda env export > environment.yml
   - $ conda env create -f environment.yml

To activate this environment, use:

   - $ source activate sasviewqt

To deactivate this environment, use:

   - $ source deactivate sasviewqt


Known problems:
---------------

    - libxml2 not installed.

