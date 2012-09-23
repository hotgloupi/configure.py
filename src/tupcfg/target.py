# -*- encoding: utf-8 -*-

import os

from .node import Node

class Target(Node):

    def __init__(self, name, dependencies):
        self.name = name
        super(Target, self).__init__(dependencies)

    #def directory(self, build):
    #    return os.path.join(build.directory, os.path.dirname(self.name))

    def path(self, **kw):
        return os.path.join(kw['build'].directory, self.name)

    def relpath(self, from_, **kw):
        if not isinstance(from_, str):
            from_ = os.path.dirname(from_.path(**kw))
        return os.path.relpath(self.path(**kw), start=from_)

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

    def execute(self, **kw):
        kw['target'] = self
        super(Target, self).execute(**kw)


    def shell_string(self, **kw):
        return self.relpath(kw['target'], **kw)
