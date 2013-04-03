# -*- encoding: utf-8 -*-

from .node import Node
from . import path

class Target(Node):

    def __init__(self, name, dependencies, additional_inputs=[], additional_outputs=[]):
        self.name = name
        super(Target, self).__init__(dependencies)
        self.additional_inputs = additional_inputs[:]
        self.additional_outputs = additional_outputs[:]


    def path(self, build):
        assert build is not None
        return path.absolute(build.directory, self.name)

    def relpath(self, from_, build):
        if not isinstance(from_, str):
            from_ = path.dirname(from_.path(build))
        return path.relative(self.path(build), start=from_)

    def directory(self, build):
        return path.dirname(self.path(build))

    def dump(self, inc=0, target=None, build=None):
        print(' ' * inc, "Target '%s':" % self.name)
        super(Target, self).dump(inc=inc+2, target=self, build=build)

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
