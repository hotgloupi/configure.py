# -*- encoding: utf-8 -*-

from types import GeneratorType
from . import path as PATH
from . import tools

class Node:
    __slots__ = ('__dependencies', 'path', 'build', 'is_directory', 'shell_formatter')
    def __init__(self,
                 build,
                 path,
                 dependencies = None,
                 is_directory = False,
                 shell_formatter = None):
        if dependencies is None:
            dependencies = []
        elif isinstance(dependencies, (tuple, GeneratorType)):
            dependencies = list(dependencies)
        assert isinstance(dependencies, list)
        assert PATH.is_absolute(path)
        self.__dependencies = dependencies
        self.path = path
        self.build = build
        self.is_directory = is_directory
        if shell_formatter is None:
            shell_formatter = lambda e: [e]
        self.shell_formatter = shell_formatter

    @property
    def dependencies(self):
        return self.__dependencies

    @property
    def directory(self):
        return PATH.dirname(self.path)

    @property
    def basename(self):
        if self.is_directory:
            raise Exception("Directories have basename")
        return PATH.basename(self.path)

    @property
    def dirname(self):
        if self.is_directory:
            return self.path
        return PATH.dirname(self.path)

    def relative_path(self, start = None):
        if start is None:
            start = self.root_directory
        return PATH.relative(self.path, start = start)

    def shell(self, start = None):
        if start is None:
            return self.shell_formatter(self.path)
        return self.shell_formatter(self.relative_path(start))

    #@property
    #def name(self):
    #    return '.'.join(self.basename.split('.')[:-1])

    def visit(self, visitor):
        tools.debug('visiting', self)
        visitor(self)
        tools.debug('visiting', self, 'dependencies', self.dependencies)
        for dep in self.dependencies:
            dep.visit(visitor)

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.path
        )

