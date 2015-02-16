import os
import hashlib

from fabric.api import env, local, run, cd, lcd, sudo, get, put
from fabric.contrib.files import exists


class VEnvCache(object):
    venv_cache_path = '/home/vagrant/venv_cache'

    def __init__(self, app_name):
        self.app_name = app_name
        run('mkdir -p {}'.format(self.venv_cache_path))

    def cache_filename(self, reqs_path):
        rv = run('sha1sum {}'.format(reqs_path))
        hash = rv.split(' ')[0]
        return '{0.venv_cache_path}/{0.app_name}_{1}.tar.gz'.format(
            self, hash)

    def get_env(self, reqs_path, target_path, env_name):
        """env_name is the folder name (w/o path) of the virtual env"""
        archive_path = self.cache_filename(reqs_path)
        full_path = os.path.join(target_path, env_name)
        if exists(archive_path):
            run('tar -xzf {} -C {}'.format(archive_path, target_path))
        else:
            run('virtualenv {}'.format(full_path))
            run('{}/bin/pip install -r {}'.format(full_path,
                reqs_path))
            run('tar -czf {} -C {} {}'.format(archive_path, target_path,
                env_name))


class Deployment(object):
    def __init__(self, app_name, build_deps=[], build_gems=[], build_pips=[],
                 repo_url=None, honcho_config=None):
        self.app_name = app_name
        self.build_path = '/srv/webapps/{}/'.format(self.app_name)
        self.src_path = os.path.join(self.build_path, self.app_name)
        self.venv_path = os.path.join(self.build_path, 'venv')
        self.python = self.exe('python')
        self.pip = self.exe('pip')
        self.build_deps = build_deps
        self.build_gems = build_gems
        self.build_pips = build_pips
        self.honcho_config = honcho_config or '/etc/{0.app_name}'.format(self)
        self.repo_url = (repo_url or
            'ssh://git@bitbucket.org/hannesstruss/{}.git'.format(app_name))

    def exe(self, name):
        return os.path.join(self.venv_path, 'bin', name)

    def prepare_app(self, branch="master"):
        for dep in self.build_deps:
            sudo('apt-get install -y {}'.format(dep))

        for gem in self.build_gems:
            sudo('gem install {}'.format(gem))

        for pip in self.build_pips:
            sudo('pip install {}'.format(pip))

        sudo('rm -rf {}'.format(self.build_path))
        sudo('mkdir -p {}'.format(self.build_path))
        sudo('chown -R vagrant: {}'.format(self.build_path))
        local('git push origin')
        run(('git clone --depth 1 {} {}'.format(self.repo_url, self.src_path)))

        with cd(self.src_path):
            run('git checkout %s' % branch)

        cache = VEnvCache(self.app_name)
        cache.get_env(reqs_path=os.path.join(self.src_path, 'requirements.txt'),
            target_path=self.build_path, env_name='venv')

        run('python -m compileall {} > /dev/null'.format(self.build_path))

    def build_deb(self):
        with cd(self.build_path):
            response = run('fpm '
                '-s dir '
                '-t deb '
                '--name {0.app_name} '
                '--version 0.1~buildtest '
                '--architecture x86_64 '
                '--exclude *.git '
                '--description "Automated build. alalala" '
                '{0.build_path}'
                .format(self))
            deb_file = response.split('"')[-2]
            local('mkdir -p debian')
            get(deb_file, './debian/')

    def deploy(self, deb_local, debug=False):
        put(deb_local, '/tmp/')
        deb_path = os.path.join('/tmp', os.path.basename(deb_local))
        sudo('dpkg -i {}'.format(deb_path))
        self.honcho_export()
        if debug:
            install_path = os.path.join(self.build_path, "mapped_source")
        else:
            install_path = self.src_path
        with cd(install_path):
            run('{0.pip} install -e .'.format(self))


    def honcho_export(self):
        with cd(self.src_path):
            sudo('{0.venv_path}/bin/honcho export '
                 '-a {0.app_name} -u {0.app_name} '
                 '-f {0.src_path}/Procfile '
                 '-e {0.honcho_config} '
                 'upstart /etc/init'
                 .format(self))

    def collect_static(self):
        with cd(self.src_path):
            run('{} manage.py collectstatic --noinput'.format(self.python))

    def django(self, cmd):
        with cd(self.src_path):
            sudo('{} manage.py {}'.format(self.python, cmd), user=self.app_name)

    def alembic_upgrade(self, revision="head"):
        with cd(self.src_path):
            sudo('{} upgrade {}'.format(self.exe('alembic'), revision),
                user=self.app_name)
