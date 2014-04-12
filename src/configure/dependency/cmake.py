from . import Dependency
from ..command import Command
from ..target import Target
from .. import platform, path

class CMakeDependency(Dependency):
    def __init__(self,
                 build,
                 name,
                 compiler,
                 source_directory,
                 build_system = None,
                 configure_target = 'Makefile',
                 verbose = True,
                 build_type = 'Release',
                 configure_variables = [],
                 libraries = [],
                 configure_env = {},
                 os_env = [],
                 install = True,
                ):
        """
            build_system:
                Defaults to makefiles, see accepted cmake generators.

            configure_target:
                The file built when cmake configure succeed.

            verbose:
                Force generated makefiles to be verbose.

            build_type:
                If not None, forwarded as CMAKE_BUILD_TYPE.

            configure_variables:
                List of (key, value) tuples forwarded as -Dkey=value.

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
                    * include_directories: (defaults to ['include'] if install
                                            is True, or [] otherwise)
                        List of include directories relative to build directory.

            configure_env:
                Environment use to configure.

            os_env:
                OS env var to forward (additionally to those of the compiler).
        """
        super().__init__(
            build,
            name = name,
            source_directory = source_directory,
        )
        self.compiler = compiler

        if build_system is None:
            if platform.IS_WINDOWS:
                if compiler.name == 'msvc':
                    import os
                    version = os.environ['VISUALSTUDIOVERSION'].split('.')[0]
                    build_system = 'Visual Studio %s' % version
                else:
                    build_system = "MinGW Makefiles"
            else:
                build_system = "Unix Makefiles"
        self.build_system = build_system
        self.verbose = verbose
        self.build_type = build_type
        self.configure_target = configure_target
        self.configure_variables = configure_variables
        self.configure_env = configure_env
        self.os_env = os_env + self.compiler.os_env
        self.install = install

        self.__libraries = []
        self.__target_libraries = []
        for lib in libraries:
            name = lib['name']
            shared = lib.get('shared', True)
            directory = lib.get('directory', install and 'lib' or '.')
            imp_directory = lib.get('imp_directory', directory)
            if install:
                directory = 'install/%s' % directory
                imp_directory = 'install/%s' % imp_directory


            cls = lib.get('class', self.compiler.Library)
            include_directories = [
                self.absolute_build_path(d)
                for d in lib.get('include_directories', self.install and ['install/include'] or [])
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
            self.__libraries.append(
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
        command = ['cmake', '--build', '.']
        if self.build_type is not None:
            command.extend(['--config', self.build_type])
        if install:
            command.extend(['--target', 'install'])
        self.__targets = [
            Command(
                "Building %s" % self.name,
                target = self.__target_libraries[0],
                additional_outputs = self.__target_libraries[1:],
                command = command,
                working_directory = self.build_path('build'),
                inputs = [self.__configure_target],
                os_env = self.os_env,
            ).target
        ]
        self.build_directory = self.absolute_build_path('build')
        self.install_directory = self.absolute_build_path('install')

    @property
    def __configure_target(self):
        command = [
            'cmake',
            path.absolute(self.source_directory),
        ]
        if self.compiler.lang == 'c':
            command.append(
                '-DCMAKE_C_COMPILER=%s' % self.compiler.binary
            )
        elif self.compiler.lang == 'c++':
            command.append(
                '-DCMAKE_CXX_COMPILER=%s' % self.compiler.binary
            )
            if self.compiler.stdlib and isinstance(self.compiler.stdlib, str):
                if self.compiler.name != 'msvc':
                    command.append(
                        '-DCMAKE_CXX_FLAGS="-stdlib=%s"' % self.compiler.stdlib
                    )
        else:
            raise Exception("Unknown compiler language")
        if self.verbose:
            command.append(
                '-DCMAKE_VERBOSE_MAKEFILE=ON'
            )
        if self.build_type is not None:
            command.append(
                '-DCMAKE_BUILD_TYPE=%s' % self.build_type
            )
        if self.compiler.name != 'msvc':
            command.extend([
                '-DCMAKE_MAKE_PROGRAM=%s' % self.build.make_program,
            ])

        command.extend([
            '-DCMAKE_SH=%s' % self.build.sh_program,
            '-DCMAKE_INSTALL_PREFIX=%s' % self.absolute_build_path('install')
        ])
        if self.compiler.name == 'msvc':
            command.extend([
                '-DCMAKE_LINKER=%s' % self.compiler.link_binary,
            ])

        def sanitize(k, v):
            if isinstance(v, bool):
                return (k, v and 'YES' or 'NO')
            return (k, v)

        command.extend(
            '-D%s=%s' % sanitize(*var)
            for var in self.configure_variables
        )
        if self.build_system is not None:
            command.extend(['-G', self.build_system])

        return Command(
            "Configure %s" % self.name,
            target = Target(self.build, self.build_path("build/CMakeFiles/cmake.check_cache")),
            command = command,
            working_directory = self.build_path('build'),
            os_env = self.os_env,
            env = self.configure_env,
        ).target


    @property
    def targets(self):
        return self.__targets

    @property
    def libraries(self):
        return self.__libraries
