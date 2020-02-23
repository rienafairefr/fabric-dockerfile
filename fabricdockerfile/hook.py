import contextlib
import os
from io import BytesIO
import sys

from dockermap.build.dockerfile import DockerFile

import __builtin__ as builtins
realimport = builtins.__import__

include = [
    ('fabric.api', 'run'),
    ('fabric.api', 'sudo'),
    ('fabric.api', 'cd'),
    ('fabric.api', 'put'),
    ('fabric.contrib.files', 'append'),
    ('fabric.contrib.files', 'upload_template'),
    ('fabric.contrib.project', 'rsync_project'),
    ('fabric.network', 'connect'),
]


def myimport(name, globals=None, locals=None, fromlist=None, *args, **kwargs):
    module = realimport(name, globals, locals, fromlist, *args, **kwargs)
    if name.startswith('fabric'):
        if fromlist:
            for fr_ in fromlist:
                if (name, fr_) in include:
                    fake_module = eval(name)
                    fake = getattr(fake_module, fr_)
                    original = getattr(module, fr_)
                    locals[fr_] = fake
                    globals[fr_] = fake
                    setattr(fake_module, '_wrap_%s' % fr_, original)
                    setattr(module, fr_, fake)
    return module


builtins.__import__ = myimport

from fabric.state import env

class AttributeString(str):
    pass


format = '%s %s %s'


class FabricApi(object):
    def run(self, command, *args, **kwargs):
        env.dockerfile.run(command)

        returned = AttributeString('')
        returned.succeeded = True
        returned.return_code = 0
        return returned

    def sudo(self, command, *args, **kwargs):
        env.dockerfile.run('sudo %s' % command)

        returned = AttributeString('')
        returned.succeeded = True
        returned.return_code = 0
        return returned

    @contextlib.contextmanager
    def cd(self, path):
        previous = env.dockerfile.command_workdir
        env.dockerfile.command_workdir = path
        yield
        env.dockerfile.command_workdir = previous

    def put(self, local_path=None, remote_path=None,
            ctx_path=None, mode=None, mirror_local_mode=True):
        if isinstance(local_path, BytesIO):
            return
        pth = ctx_path if ctx_path else local_path
        if not os.path.exists(pth):
            raise ValueError('local file does not exist %s' % pth)
        if pth.startswith('../tools'):
            # otherwise, outside of build context
            pth2 = os.path.relpath(pth, '../tools')
            pth = os.path.join('template/tools', pth2)
        env.dockerfile.prefix('COPY', pth, remote_path)
        env.files.append(pth)
        if mode:
            env.dockerfile.run('chmod %s %s' % (oct(mode), remote_path))



class FabricContribFiles(object):
    def __init__(self, fab):
        self.fabric = fab

    def append(self, filename, text):
        text = text.replace('\n','\\n')
        text = text.replace('\r', '\\r')
        self.fabric.api.run('echo "%s" >> %s' % (text, filename))


class FabricContribProject(object):
    def __init__(self, fab):
        self.fabric = fab

    def rsync_project(self,
                      remote_dir,
                      local_dir=None,
                      *args, **kwargs
                      ):
        env.dockerfile.comment('rsync %s %s' % (args, kwargs))
        self.fabric.api.put(local_dir, remote_dir)


class FabricContrib(object):
    def __init__(self, fab):
        self.files = FabricContribFiles(fab)
        self.project = FabricContribProject(fab)


class FabricNetwork(object):
    def connect(self, *args, **kwargs):
        pass


class Fabric(object):
    def __init__(self):
        self.api = FabricApi()
        self.contrib = FabricContrib(self)
        self.network = FabricNetwork()


fabric = Fabric()





def start(dockerfile=None):
    if dockerfile is None:
        dockerfile = DockerFile()
    env.dockerfile = dockerfile
