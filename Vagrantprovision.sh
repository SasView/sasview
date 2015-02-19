#! /bin/bash

sed -i 's,http://us.archive.ubuntu.com/ubuntu/,mirror://mirrors.ubuntu.com/mirrors.txt,' /etc/apt/sources.list
apt-get update

apt-get install -y xvfb git python-pip pkg-config libfreetype6-dev libpng-dev python-dev python-wxtools pylint python-matplotlib python-numpy python-sphinx python-xmlrunner python-pisa python-setuptools python-scipy python-pyparsing python-html5lib python-reportlab python-lxml python-pil
pip install bumps comtypes periodictable 

cat >> ~vagrant/.bashrc <<EOF
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8
sasview-compile() {
cd /vagrant
sh ./build_tools/jenkins_linux_build.sh
}
sasview-test() {
cd /vagrant
sh ./build_tools/jenkins_linux_test.sh
}
EOF
