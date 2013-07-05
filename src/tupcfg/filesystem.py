# -*- encoding: utf-8 -*-

from .command import Command
from .source import Source
from .target import Target

from . import path

class Copy(Command):
    @property
    def action(self):
        return "Copying %s to" % self.dependencies[0]
    def command(self, **kw):
        return ['cp', self.dependencies, kw['target']]

class Filesystem:
    """Filesystem operations on a build.
    """
    def __init__(self, build):
        self.build = build

    def copy(self, src, dest=None):
        """
        """
        if dest is None:
            dest = src
        return self.build.add_target(
            Target(dest, Copy(Source(src)))
        )
#
#
