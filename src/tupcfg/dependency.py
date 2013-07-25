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
                 dependencies: "Dependencies" = [],
                 build_config: "strings that make this build specific" = []):
        self.name = name
        self.directory = directory
        self.build_config = build_config
        self.__build = None
        super(Dependency, self).__init__(dependencies)

    def set_build(self, build):
        self.__build = build

    @property
    def resolved_build(self):
        return self.__build

    def build_path(self, *args, abs = False):
        """Build a path relative to the dependency build directory.

        Since the build is not known until dependencies have been checked by
        the project, this function return a "lazy" resolver.
        """
        return self._Path(
            self,
            *(tuple(self.build_config) + args),
            abs = abs
        )

    def source_path(self, *args, abs = False):
        return self._Path(self, *args, abs = abs, from_source = True)

    class _Path:
        def __init__(self, dependency, *args, abs = False, from_source = False):
            self.dependency = dependency
            self.args = args
            self.abs = abs
            self.from_source = from_source

        def shell_string(self, build=None, cwd=None):
            return str(self)

        def __str__(self):
            if self.dependency.resolved_build is None:
                bdir = '<unresolved "%s" %s directory>' % (
                    self.dependency.name,
                    self.from_source and 'source' or 'build'
                )
            else:
                bdir = path.absolute(self.dependency.resolved_build.directory)

            if self.from_source:
                res = path.join(self.dependency.source_directory, *self.args)
            else:
                res = path.join(bdir, self.dependency.directory, *self.args)


            if self.abs:
                return path.absolute(res)
            else:
                return path.relative(res, start = bdir)

