# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://vagrantcloud.com/search.
  config.vm.box = "generic/ubuntu2310"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # NOTE: This will enable public access to the opened port
  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 3012, host: 3012

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine and only allow access
  # via 127.0.0.1 to disable public access
  # config.vm.network "forwarded_port", guest: 80, host: 8080, host_ip: "127.0.0.1"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Disable the default share of the current code directory. Doing this
  # provides improved isolation between the vagrant box and your host
  # by making sure your Vagrantfile isn't accessible to the vagrant box.
  # If you use this you may want to enable additional shared subfolders as
  # shown above.
  config.vm.synced_folder ".", "/vagrant", disabled: false

  synced_folder_mapping = {
    PATHS_INPUT_FOLDER: '/app/inputs',
    PATHS_MOVIES_FOLDER: '/app/movies',
    PATHS_SERIES_FOLDER: '/app/series',
    PATHS_BACKUP_FOLDER: '/app/backup',
    ARCHIVE_BACKUP_FOLDER: '/app/archive/source',
    ARCHIVE_MOVIES_ARCHIVE_FOLDER: '/app/archive/dest',
    LOGGER_LOG_FOLDER: '/app/logs'
  }.transform_keys(&:to_s)

  synced_folder_mapping.each do |env_name, guest_path|
    env_value = ENV[env_name]
    raise "Missing environment variable #{env_name}" if env_value.nil?
    config.vm.synced_folder ENV[env_name], guest_path
  end

  config.vm.synced_folder './movie_pipeline/jobs/data', '/opt/cronicle/data'

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  
  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    # vb.gui = true

    # cf https://gist.github.com/z-burke/080b28075f336c637b94009c076d65ab
  
    # Customize the amount of memory on the VM:
    vb.memory = "2048"
    vb.cpus = 8

    # Enable 3D acceleration for better Desktop experience
    vb.customize ["modifyvm", :id, "--accelerate3d", "on"]

    # Specify the amount of VRAM to allocate to the VM
    vb.customize ["modifyvm", :id, "--vram", "128"]
    
    # Use the VMSVGA graphics controller
    vb.customize ["modifyvm", :id, "--graphicscontroller", "vmsvga"]
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Enable provisioning with a shell script. Additional provisioners such as
  # Ansible, Chef, Docker, Puppet and Salt are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "bootstrap", type: "shell", preserve_order: true, inline: <<-SHELL
    #!/bin/bash
    set -euxo pipefail

    apt-get update
    apt-get install -y curl tini ffmpeg pipx

    # Install movie_pipeline
    pipx install /vagrant/dist/movie_pipeline-0.2.6.tar.gz
    pipx ensurepath

    # Init movie_pipeline environment

    mkdir -p /app/inputs /app/movies /app/series /app/backup /app/logs /app/archive/source /app/archive/dest ~/.movie_pipeline \
      && touch /app/logs/log.txt

    echo '' > ~/.movie_pipeline/config.env
    echo Paths__movies_folder=/app/movies >> ~/.movie_pipeline/config.env
    echo Paths__series_folder=/app/series >> ~/.movie_pipeline/config.env
    echo Paths__backup_folder=/app/backup >> ~/.movie_pipeline/config.env
    echo '' >> ~/.movie_pipeline/config.env
    echo Archive__base_backup_path=/app/archive/source  >> ~/.movie_pipeline/config.env
    echo Archive__movies_archive_folder=/app/archive/dest  >> ~/.movie_pipeline/config.env
    echo Archive__max_retention_in_s=33_000_000 >> ~/.movie_pipeline/config.env
    echo '' >> ~/.movie_pipeline/config.env
    echo Logger__file_path=/app/logs/log.txt >> ~/.movie_pipeline/config.env

    # Install node

    apt-get remove -y nodejs npm

    curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh \
      && bash nodesource_setup.sh \
      && rm nodesource_setup.sh \
      && apt-get install -y nodejs \
      && node -v \
      && npm -v

    # Install cronicle
    # cf https://github.com/jhuckaby/Cronicle/blob/master/docs/Setup.md & https://github.com/cronicle-edge/cronicle-edge/blob/main/Dockerfile

    mkdir -p /opt/cronicle/tmp \
      && cd /opt/cronicle/tmp \
      && curl -sSL https://github.com/cronicle-edge/cronicle-edge/archive/refs/tags/v1.9.4.tar.gz | tar zxvf - --strip-components 1 \
      && ./bundle /opt/cronicle -f --mysql --pgsql --s3 --sqlite --tools \
      && rm -rf /opt/cronicle/tmp \
      && cd /opt/cronicle

    echo '' > /etc/environment
    echo PATH="/opt/cronicle/bin:/root/.local/bin/:${PATH}" >> /etc/environment
    echo CRONICLE_foreground=1 >> /etc/environment
    echo CRONICLE_echo=1 >> /etc/environment
    echo TZ=Europe/Paris >> /etc/environment
    echo CRONICLE_manager=1 >> /etc/environment
  SHELL

  config.vm.provision "shell", run: "always",  after: "bootstrap", inline: <<-SHELL
    #!/bin/bash

    # Load environment variables in this session
    for env in $( cat /etc/environment ); do export $(echo $env | sed -e 's/"//g'); done

    # Start cronicle
    /usr/bin/tini -s -- manager
  SHELL
end
