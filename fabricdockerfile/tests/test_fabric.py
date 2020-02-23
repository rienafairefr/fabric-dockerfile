import fabricdockerfile.hook as hook

from fabric.state import env
from fabric.tasks import execute
from fabric.decorators import task
from fabric.operations import run


@task
def run_task():
    run('echo "key=value" > /etc/file.conf')


def test_task():
    hook.start()
    env.host = 'host.test'
    env.host_string = 'user@%s:%i' % (env.host, 22)
    execute(run_task)
    print(env.dockerfile)
