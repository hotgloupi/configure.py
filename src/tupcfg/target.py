# -*- encoding: utf-8 -*-

import os

from .node import Node

class Target(Node):

    def __init__(self, name, dependencies):
        self.name = name
        super(Target, self).__init__(dependencies)

    def directory(self, build):
        return os.path.join(build.directory, os.path.dirname(self.name))

    def dump(self, inc=0, **kwargs):
        print(' ' * inc, "Target '%s':" % self.name)
        kwargs['inc'] = inc + 2
        kwargs['target'] = self
        super(Target, self).dump(**kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.name
        )

    def execute(self, **kwargs):
        kwargs['target'] = self
        super(Target, self).execute(**kwargs)


    def shell_string(self, **kwargs):
        return os.path.relpath(
            os.path.join(kwargs['build'].directory, self.name),
            start=kwargs['target'].directory(kwargs['build'])
        )
