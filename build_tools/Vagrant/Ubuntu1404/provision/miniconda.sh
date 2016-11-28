#! /bin/bash

# Install miniconda
# download - wget
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh

# To set up through vagrant provision - seems however to cause read/write sudo issues later when pip or conda install
#wget https://repo.continuum.io/archive/Anaconda2-4.2.0-Linux-x86_64.sh
#chmod +x Anaconda2-4.2.0-Linux-x86_64.sh
#mv Anaconda2-4.2.0-Linux-x86_64.sh anaconda.sh
#./anaconda.sh -b -p /home/vagrant/anaconda

