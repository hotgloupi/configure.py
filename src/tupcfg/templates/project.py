# -*- encoding: utf-8 -*-

"""This file defines the default variables for your project and the configure
function.

All variable defined here will be available in the configure function, only if
their name is in the form [A-Z][_A-Z0-9]* (upper case, underscore and digits).

If a variable is evaluated to False, and if a variable with the same name but
suffixed with "_CMD" exists, it will be evaluated as follow:
    * if it is a string or a list, it launches a shell command
    * if it is a python function, it will be called with a project and a build
      instances as arguments.

For example:
     >>> VERSION_NAME = None                              # necessary
     >>> VERSION_NAME_CMD = "git --describe"              # retreive with git
     >>> VERSION_NAME_CMD = ["git", "--describe"]         # safer syntax
     >>> def myPythonFunction(project) : return 32        # simple function
     ...
     >>> VERSION_NAME_CMD = _myPythonFunction

and in the configure function, you do:
    >>> print(project.env.VERSION_NAME)

All variables defined here can be overridden by:
    * The cache (modified through ./configure -DVAR=value)
    * the OS environment

For example, if `NAME` is defined to 'original' in this script,
    >>> project.env.NAME == 'original'
    True

But, if you run:
    $ ./configure -DNAME="cached"
Then, the variable `NAME` will always be evaluated to "cached", at the opposite
of using environment:
    $ NAME="only_for_this_time" ./configure

"""

# The project name
NAME = "%(PROJECT_NAME)s"

# The version name (could be "alpha" for example)
VERSION_NAME = "%(PROJECT_VERSION_NAME)s"

from tupcfg import Source
from tupcfg import Target
from tupcfg import Command
from tupcfg import Build

class BuildObject(Command):

    def command(self, **kw):
        return [
            'gcc',
            '-c', self.dependencies[0],
            '-o', kw['target'],
        ]

class LinkExecutable(Command):
    def command(self, **kw):
        return [
            'gcc',
            self.dependencies[0],
            '-o', kw['target'],
        ]

def configure(project, build):
    print("Configuring project", project.env.NAME, 'in', build.directory)
    srcs = list(Source(src) for src in ['test.c', 'main.c'])
    objs = [
        Target(src.name + '.o', BuildObject(src)) for src in srcs
    ]
    target = Target('test', LinkExecutable(objs))
    build.add_target(target)
    build.dump(project)
    build.execute(project)
