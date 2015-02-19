# -*- mode: ruby -*-
# vi: set ft=ruby :

# This allows you to build sasview using vagrant 
# for the moment you can build Ubuntu on any platform supported by vagrant
# (Linux, Mac, Windows)
# You will need VirtualBox as well. 
# Download pages:
# http://www.vagrantup.com/downloads
# https://www.virtualbox.org/wiki/Downloads

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu1404"
  config.vm.box_url = "https://github.com/hnakamur/packer-templates/releases/download/v1.0.2/ubuntu-14-04-x64-virtualbox.box"
  #config.vm.box = "fedora19"
  #config.vm.box_url = "https://dl.dropboxusercontent.com/u/86066173/fedora-19.box"
  #config.vm.box = "fedora20"
  #config.vm.box_url = "https://dl.dropboxusercontent.com/u/15733306/vagrant/fedora-20-netinst-2014_01_05-minimal-puppet-guestadditions.box"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
  #  # Display the VirtualBox GUI when booting the machine
  #  vb.gui = true
  #
  #  # Customize the amount of memory on the VM:
     vb.memory = "1024"
     vb.cpus = "1"
  end
  #
  config.vm.provision :shell, :path => "Vagrantprovision.sh"
end
