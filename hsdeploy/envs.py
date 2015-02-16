import os

from fabric.api import env, local, lcd


def get_vagrant_ssh_config():
    result = local('vagrant ssh-config', capture=True)
    result = [line.strip().split(' ', 1) for line in result.splitlines()[1:]]
    result = [(k, v.strip('"')) for k, v in result]
    return dict(result)


def vagrant_env():
    cfg = get_vagrant_ssh_config()
    env.user = cfg['User']
    env.hosts = ['{HostName}:{Port}'.format(**cfg)]
    env.key_filename = cfg['IdentityFile']
    env.forward_agent = True


def buildbox():
    with lcd(os.path.join(os.path.dirname(__file__), '..')):
        vagrant_env()


try:
    from localenvs import *
except ImportError:
    pass
