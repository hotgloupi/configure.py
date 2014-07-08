# -*- encoding: utf-8 -*-

from .. import path as PATH
from .. import platform
from ..target import Target

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
                 compiler = None,
                 dependencies = [],
                 build_config = tuple(),
                 libraries = []):
        """
        name: Dependency name
        source_directory: Directory name
        dependencies: Dependencies
        build_config: strings that make this build specific
        libraries:
            List of dict used to build libraries instances, availables keys:
                * name:
                    The name without any 'lib' prefix or extensions.
                * prefix: (defaults to lib, except on windows if the
                           compiler is not gcc and shared is False)
                    The prefix of the built library.
                * shared: (defaults to True)
                    Whether or not the library is shared.
                * directory: (defaults to '.')
                    Where the library will be built relatively to the cmake
                    build directory (if install is False) or to the install
                    directory
                * imp_directory: (defaults to directory)
                    Where the "imp" library is generated (on windows),
                    relative to the install directory (if install is True)
                    or to the build directory otherwise.
                * imp_filename: (defaults to {prefix}{name}.lib)
                    On Windows, choose the name of the imp filename.
                * class: (defaults to compiler.Library)
                    Type of the library.
                * source_include_directories: (defaults to [])
                    List of include directories relative to source directory.
                * include_directories: (defaults to ['install/include'] if install
                                        is True, or [] otherwise)
                    List of include directories relative to build directory.
        """
        from configure.build import Build
        assert isinstance(build, Build)
        self.build = build
        self.name = name
        self.source_directory = source_directory
        self.build_config = tuple(build_config)
        self.dependencies = dependencies
        self.compiler = compiler

        self.build_directory = self.absolute_build_path('build')
        self.install_directory = self.absolute_build_path('install')
        self.libraries = []
        self.__target_libraries = []
        for lib in libraries:
            name = lib['name']
            shared = lib.get('shared', True)
            directory = lib.get('directory', 'lib')
            imp_directory = lib.get('imp_directory', directory)
            directory = 'install/%s' % directory
            imp_directory = 'install/%s' % imp_directory


            cls = lib.get('class', self.compiler.Library)
            include_directories = [
                self.absolute_build_path(d)
                for d in lib.get('include_directories', ['install/include'])
            ]
            include_directories.extend([
                self.absolute_source_path(d) for d in lib.get('source_include_directories', [])
            ])


            ext = self.compiler.library_extension(shared)
            if platform.IS_WINDOWS and not (self.compiler.name == 'gcc' and not shared):
                prefix = ''
            else:
                prefix = 'lib'
            prefix = lib.get('prefix', prefix)
            filename = '%s%s.%s' % (prefix, name, ext)
            path = self.build_path(directory, filename)
            if platform.IS_WINDOWS:
                imp_filename = lib.get('imp_filename', '%s%s.%s' % (prefix, name, 'lib'))
                link_files = [self.absolute_build_path(imp_directory, imp_filename)]
            else:
                link_files = None
            self.libraries.append(
                cls(
                    self.name,
                    self.compiler,
                    shared = shared,
                    search_binary_files = False,
                    include_directories = include_directories,
                    directories = [self.absolute_build_path(imp_directory)],
                    files = [self.absolute_build_path(directory, filename)],
                    link_files = link_files,
                    save_env_vars = False,
                )
            )
            self.__target_libraries.append(Target(self.build, path))

    @property
    def target_libraries(self):
        return self.__target_libraries

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

from .cmake import CMakeDependency
from .autotools import AutotoolsDependency
