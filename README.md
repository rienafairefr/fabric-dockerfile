Fabric-Dockerfile
=================


For a variety of reasons, it can be interesting to run a fabric task and
be able to generate a Dockerfile that contains instructions
as if the `fab` was run targetting a host that is a Docker container.

Use cases:

- Migrating from manually deployed services to a container-based infrastructure,
this tool can help you generate a Dockerfile that matches your already
developed deployment code

- Unit testing fabric tasks


Usage
-----

By importing the hook,

```
import fabricdockerfile.hook
```

You will patch your \_\_import\_\_, and subsequently all calls to something in
the `fabric` namespace should call special methods that will register the
fabric steps in the DockerFile. The resulting dockerfile is saved
in the `env` global state

Example:
```
import fabricdockerfile.hook
from my_tasks import deploy_server
from fabric.tasks import execute
from fabric.state import env

execute(deploy_server)

```

Limitations
-----------

- If your Fabric tasks make some different things depending on the role, host or host string,
then you should make different calls with the appropriate role or host set up and generate multiple DockerFiles
- Not all `fabric` namespace functions are implemented, and some are implemented poorly
