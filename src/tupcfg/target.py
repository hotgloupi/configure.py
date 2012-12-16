# -*- encoding: utf-8 -*-

from .node import Node
from . import path

class Target(Node):

    def __init__(self, name, dependencies):
        self.name = name
        super(Target, self).__init__(dependencies)

    def path(self, build):
        assert build is not None
        return path.absolute(build.directory, self.name)

    def relpath(self, from_, build):
        if not isinstance(from_, str):
            from_ = path.dirname(from_.path(build))
        return path.relative(self.path(build), start=from_)

    def dump(self, inc=0, **kw):
        print(' ' * inc, "Target '%s':" % self.name)
        kw['inc'] = inc + 2
        kw['target'] = self
        super(Target, self).dump(**kw)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.name
        )

    def execute(self, target=None, build=None):
        super(Target, self).execute(target=self, build=build)


    def shell_string(self, target=None, build=None):
        return self.relpath(target, build=build)
