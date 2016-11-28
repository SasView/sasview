#! /bin/bash

# Install basic developer tools 

sudo apt-get update
sudo apt-get install -y git
sudo apt-get install -y vim build-essential


sudo apt-get install dpkg-dev fakeroot lintian

# Now with mpistuff 
sudo apt-get install -y openmpi-bin openmpi-doc libopenmpi-dev

#Install viewer to nexus files 
sudo apt-get install -y hdfview

# Install PyCharm community edition
sudo add-apt-repository ppa:mystic-mirage/pycharm
sudo apt-get update
sudo apt-get install -y --force-yes pycharm-community 

