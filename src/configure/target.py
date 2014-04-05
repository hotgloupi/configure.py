# -*- encoding: utf-8 -*-

from .node import Node
from . import path as PATH

class Target(Node):

    #__slots__ = ()

    def __init__(self, build, path, dependencies = None, shell_formatter = None):
        from .build import Build
        assert isinstance(build, Build)
        assert not PATH.is_absolute(path)
        super().__init__(
            build = build,
            path = PATH.absolute(build.directory, path),
            dependencies = dependencies,
            is_directory = False,
            shell_formatter = shell_formatter,
        )
        build.add_target(self)

    @property
    def root_directory(self):
        return self.build.directory
