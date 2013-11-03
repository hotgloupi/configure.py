# -*- encoding: utf-8 -*-

from . import path as PATH
from .node import Node

class Source(Node):
    __slots__ = ()

    def __init__(self, build, path, dependencies = None):
        super().__init__(
            build,
            PATH.absolute(build.project.directory, path),
            dependencies = dependencies
        )

    @property
    def root_directory(self):
        return self.build.project.directory

