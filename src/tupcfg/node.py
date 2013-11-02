# -*- encoding: utf-8 -*-

from types import GeneratorType
from . import path as PATH
from . import tools

class Node:
    __slots__ = ('__dependencies', 'path', 'build', 'relative_path')
    def __init__(self, build, path, dependencies = None):
        if dependencies is None:
            dependencies = []
        elif isinstance(dependencies, (tuple, GeneratorType)):
            dependencies = list(dependencies)
        assert isinstance(dependencies, list)
        assert PATH.is_absolute(path)
        self.__dependencies = dependencies
        self.path = path
        self.build = build
        self.relative_path = PATH.relative(
            path,
            start = self._root_directory()
        )

    @property
    def dependencies(self):
        return self.__dependencies

    @property
    def directory(self):
        return PATH.dirname(self.path)

    @property
    def basename(self):
        return PATH.basename(self.path)

    @property
    def dirname(self):
        return PATH.dirname(self.path)

    def make_relative_path(self, start):
        return PATH.relative(self.path, start = start)
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
            self.relative_path
        )
