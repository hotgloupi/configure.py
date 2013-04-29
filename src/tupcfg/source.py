# -*- encoding: utf-8 -*-

from . import path
from .node import Node

class Source(Node):

    def __init__(self, filename):
        if isinstance(filename, list):
            raise Exception("Give a list of Source, not the opposite")
        self.filename = filename
        super(Source, self).__init__(None)

    def path(self, build):
        return path.absolute(build.root_directory, self.filename)

    def relpath(self, from_, build):
        if not isinstance(from_, str):
            from_ = path.dirname(from_.path(build))
        return path.relative(self.path(build), start=from_)

    @property
    def name(self):
        return '.'.join(self.filename.split('.')[:-1])


    def __str__(self):
        return self.filename

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.filename
        )

    def shell_string(self, cwd=None, build=None):
        return self.relpath(cwd, build)

