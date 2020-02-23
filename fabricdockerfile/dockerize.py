import errno
import os
# noinspection PyUnresolvedReferences
import re
import shutil
import tempfile

import hook
# noinspection PyUnresolvedReferences
from fabfile import dev, prod, ci
from dockermap.api import DockerFile
# noinspection PyUnresolvedReferences
from fabric.state import env
from fabric.tasks import execute

from install_lib.config import load_env
from install_lib.guests import srvoar, srvwww, srvdhcp, srvssh, srveh, srvnfs
from install_lib.guests.srvdns import setup_server_dns
from install_lib.guests.srvldap import setup_server_ldap
from jinja2 import Environment, FileSystemLoader

dockerfile = DockerFile()

platform = 'dev'
docker_dir = None

rewrites = {
    'RUN /etc/init.d.*': lambda l: '',
    'RUN ifup\s.*': lambda l: '',
    'RUN lsb_release.*': lambda l: '',
    'RUN mount -a.*': lambda l: '',
    'RUN crontab': lambda l: '',
    'RUN cat ~senslabeh': lambda l: '',
    'RUN reboot': lambda l: '',
    'RUN quotacheck': lambda l: l.strip() + ' | true\n',
    'RUN sed.*/etc/locale.gen': lambda l: 'RUN apt-get install locales\n'+l,
    'RUN wget*': lambda l: 'RUN apt-get install -yqq wget\n'+l
}


def filter_file(input_path, output_path=None):
    """ remove from file lines that verify func(line)"""
    if output_path is None:
        output_path = input_path
    with open(input_path, 'r') as input_file:
        lines = input_file.readlines()
    with open(output_path, 'w') as output_file:
        for line in lines:
            found = False
            for rewrite, rewrite_func in rewrites.items():
                if re.match(rewrite, line):
                    found = True
                    output_file.write(rewrite_func(line))
            if not found:
                output_file.write(line)


def copy_tree(file1, file2, verify=True):
    if verify and \
            not any(el.startswith(file1) for el in env.files):
        return
    try:
        shutil.rmtree(file2)
    except:
        pass
    shutil.copytree(file1, file2)


def treat_one(role, value, func):
    global docker_dir, env

    env.dockerfile = DockerFile(baseimage='iot-lab-base-guest')
    # entry point
    env.dockerfile.prefix('COPY', 'docker_entrypoint.py', 'docker_entrypoint.py')

    env.docker_compose_dir = os.path.join('dockers', role)
    env.docker_dir = os.path.join(env.docker_compose_dir, value)
    env.templates = []
    env.files = []

    execute(func)

    try:
        os.makedirs(env.docker_dir)
    except:
        pass

    copy_tree('template', os.path.join(env.docker_dir, 'template'))
    copy_tree('config', os.path.join(env.docker_compose_dir, 'config'), verify=False)
    copy_tree('../tools', os.path.join(env.docker_dir, 'template/tools'), verify=False)

    template_dir = "template/docker/"

    jenv = Environment(loader=FileSystemLoader(template_dir))

    template_entry_point = 'docker_entrypoint.py.jinja2'
    entry_point = os.path.join(env.docker_dir, 'docker_entrypoint.py')
    try:
        os.makedirs(os.path.dirname(entry_point))
    except:
        pass

    with open(entry_point, 'w') as entry_point_file, \
            open('docker_entrypoint.py', 'r') as header_entry_point_file:
        header = header_entry_point_file.read()
        text = jenv.get_template(template_entry_point).render(templates=env.templates)
        entry_point_file.write(header+'\n'+text)


    docker_path = os.path.join(env.docker_dir, 'Dockerfile')

    env.dockerfile.save(docker_path)

    filter_file(docker_path)


    compose_text = jenv.get_template('docker-compose.yml.jinja2').render(role=role)
    with open(os.path.join(env.docker_compose_dir, 'docker-compose.yml'), 'w') as compose:
        compose.write(compose_text)


roles = {'client': 'devunittest.iot-lab.info',
         'master': 'devunittest-master.iot-lab.info',
         'full': 'devunittest-full.iot-lab.info'}


def treat_role(role):
    if role in ('master', 'full'):
        treat_one(role, 'srvdns', setup_server_dns)
        treat_one(role, 'srvldap', setup_server_ldap)
        treat_one(role, 'srvoar', srvoar.setup)
        treat_one(role, 'srvwww', srvwww.setup)

    treat_one(role, 'srvnfs', srvnfs.setup)

    if role in ('client', 'full'):
        treat_one(role, 'srvdhcp', srvdhcp.setup)
        treat_one(role, 'srvssh', srvssh.setup_server_ssh)
        treat_one(role, 'srveh', srveh.setup)

hook.start_mock()
env.platform = 'infra'
for role, host in roles.items():
    env.host = host
    env.host_string = 'root@%s:2222' % host
    load_env('config/dev.cfg')
    treat_role(role)
hook.start_mock()