# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "lucid64"
  config.vm.box_url = "http://files.vagrantup.com/lucid64.box"

  config.vm.synced_folder "salt", "/srv/salt"

  config.vm.provision :salt do |salt|
    salt.run_highstate = true
    salt.minion_config = "salt/minion.conf"
    salt.verbose = true
  end
end
