# -*- encoding: utf-8 -*-

from tupcfg import path as PATH

class Dependency:
    """Represent a project or a build dependency.

    Dependencies are checked and built separatly, as they are externals to the
    project.
    They may depend on other dependencies, libraries, compilers and they
    provide one or more targets.
    """

    def __init__(self,
                 build,
                 name,
                 source_directory,
                 dependencies = [],
                 build_config = tuple()):
        """
        name: Dependency name
        source_directory: Directory name
        dependencies: Dependencies
        build_config: strings that make this build specific
        """
        from tupcfg.build import Build
        assert isinstance(build, Build)
        self.build = build

        self.name = name
        self.source_directory = source_directory
        self.build_config = tuple(build_config)
        self.dependencies = dependencies


    def build_path(self, *args):
        """Build a path relative to the dependency build directory.

        Since the build is not known until dependencies have been checked by
        the project, this function return a "lazy" resolver.
        """
        components = self.build_config + args
        return PATH.join(
            self.name,
            *components
        )

    def absolute_build_path(self, *args):
        return PATH.absolute(
            self.build.directory,
            self.build_path(*args)
        )

    def source_path(self, *args):
        return PATH.join(
            self.source_directory,
            *args
        )

    def absolute_source_path(self, *args):
        return PATH.absolute(
            self.build.project.directory,
            self.source_path(*args)
        )

