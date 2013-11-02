# -*- encoding: utf-8 -*-

from .node import Node
from . import path as PATH

class Target(Node):

    __slots__ = ()

    def __init__(self, build, path):
        from .build import Build
        assert isinstance(build, Build)
        assert not PATH.is_absolute(path)
        super().__init__(build, PATH.absolute(build.directory, path))
        build.add_target(self)

    def _root_directory(self):
        return self.build.directory

    def __str__(self):
        return str(self.relative_path)
