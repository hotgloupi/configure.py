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


            configure_env:
                Environment use to configure.

            os_env:
                OS env var to forward (additionally to those of the compiler).
        """
        super().__init__(
            build,
            name = name,
            source_directory = source_directory,
            libraries = libraries,
            compiler = compiler,
        )

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

        command = ['cmake', '--build', '.']
        if self.build_type is not None:
            command.extend(['--config', self.build_type])
        command.extend(['--target', 'install'])
        self.targets = [
            Command(
                "Building %s" % self.name,
                target = self.target_libraries[0],
                additional_outputs = self.target_libraries[1:],
                command = command,
                working_directory = self.build_path('build'),
                inputs = [self.__configure_target],
                os_env = self.os_env,
            ).target
        ]

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
