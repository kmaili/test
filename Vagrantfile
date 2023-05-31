Vagrant.configure("2") do |config|
  config.vagrant.plugins = ['vagrant-disksize','vagrant-docker-compose']
  config.vm.box = "ubuntu/bionic64"
  config.disksize.size = '15GB'
  config.vm.network "private_network", ip: "192.168.33.160"
  config.vm.hostname  = 'dauthenticator1'
  config.vm.provider "virtualbox" do |vb|
	  vb.memory=4096
	  vb.name  = 'dauthenticator1'
  end
  config.vm.provision :docker
  config.vm.provision :docker_compose, yml: "/vagrant/local.yml", run: "always"
end