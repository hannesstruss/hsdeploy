default_pkgs:
  pkg.installed:
    - names:
      - build-essential
      - libpq-dev
      - python-dev
      - git-core

fpm:
  gem.installed:
    - require:
      - pkg: default_pkgs

python-pip:
  pkg.installed

pip:
  pip.installed:
    - upgrade: True
    - require:
      - pkg: python-pip

virtualenv:
  pip.installed:
    - require:
      - pip: pip

/home/vagrant/.pip/pip.conf:
  file.managed:
    - source: salt://pip.conf
    - user: vagrant
    - group: vagrant

/home/vagrant/.ssh/config:
  file.managed:
    - source: salt://ssh_config
    - user: vagrant
    - group: vagrant
