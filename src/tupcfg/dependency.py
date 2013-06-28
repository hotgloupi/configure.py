# -*- encoding: utf-8 -*-

from .node import Node
from . import path

class Dependency(Node):
    """Represent a project or a build dependency.

    Dependencies are checked and built separatly, as they are externals to the
    project.
    They may depend on other dependencies, libraries, compilers and they
    provide one or more targets.
    """

    def __init__(self,
                 name: "Dependency name",
                 directory: "Directory name",
                 dependencies: "Dependencies" = [],):
        self.name = name
        self.directory = directory
        self.__build = None
        super(Dependency, self).__init__(dependencies)

    def set_build(self, build):
        self.__build = build

    @property
    def resolved_build(self):
        return self.__build

    def build_path(self, *args):
        """Build a path relative to the dependency build directory.

        Since the build is not known until dependencies have been checked by
        the project, this function return a "lazy" resolver.
        """
        return self._Path(self, *args)

    class _Path:
        def __init__(self, dependency, *args):
            self.dependency = dependency
            self.args = args

        def shell_string(self, build=None, cwd=None):
            return str(self)

        def __str__(self):
            if self.dependency.resolved_build is None:
                bdir = '<"%s" build directory>' % self.dependency.name
            else:
                bdir = path.absolute(self.dependency.resolved_build.directory)
            return path.join(
                bdir,
                self.dependency.directory,
                *self.args
            )
