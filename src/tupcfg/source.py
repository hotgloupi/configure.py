# -*- encoding: utf-8 -*-

import os

from .node import Node

class Source(Node):

    def __init__(self, filename):
        if isinstance(filename, list):
            raise Exception("Give a list of Source, not the opposite")
        self.filename = filename
        super(Source, self).__init__(None)

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

    def shell_string(self, **kwargs):
        return os.path.relpath(
            os.path.join(kwargs['build'].root_directory, self.filename),
            start=kwargs['target'].directory(kwargs['build'])
        )

