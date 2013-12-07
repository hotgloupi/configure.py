# -*- encoding: utf-8 -*-

from ..library import Library
from tupcfg import platform, path, tools
from tupcfg import Dependency, Target
from tupcfg.command import Command

class SDLLibrary(Library):
    def __init__(self, compiler, components=[], **kw):
        super(SDLLibrary, self).__init__(
            'SDL',
            compiler,
            find_includes = ['SDL/SDL.h'],
            shared = kw.get('shared', True),
        )
        self.components = list(
            Library('SDL_' + c, compiler, shared = kw.get('shared', True))
            for c in components
        )
        if platform.IS_MACOSX:
            self.components.append(Library('SDLmain', compiler, shared = False)) # Fixture from SDL is needed

    @property
    def libraries(self):
        return [self] + self.components



class _Dependency(Dependency):
    __targets = None
    @property
    def install_directory(self):
        return self.build_path('install')

    @property
    def absolute_install_directory(self):
        return path.absolute(self.build.directory, self.install_directory)

    @property
    def library_directory(self):
        if self.shared and platform.IS_WINDOWS:
            dir = 'bin'
        else:
            dir = 'lib'
        return path.join(self.install_directory, dir)

    @property
    def absolute_library_directory(self):
        return path.absolute(self.build.directory, self.library_directory)

    @property
    def library_path(self):
        return path.join(self.library_directory, self.library_filename)

    @property
    def absolute_library_path(self):
        return path.absolute(self.build.directory, self.library_path)

    @property
    def compiler_binary(self):
        if platform.IS_MACOSX:
            # on macosx SDL does compile with the default compiler
            return 'gcc'
        return self.compiler.binary

    @property
    def targets(self):
        if self.__targets is None:
            self.__targets = self._targets()
        return self.__targets

class SDLDependency(_Dependency):
    def __init__(self, build, compiler, source_directory, shared = True):
        super().__init__(build, "SDL", source_directory)
        self.shared = shared
        self.compiler = compiler
        ext = self.compiler.library_extension(shared)
        if platform.IS_WINDOWS:
            prefix = ''
        else:
            prefix = 'lib'
        self.library_filename = '%sSDL2.%s' % (prefix, ext)
        self.__libraries = None

    def _targets(self):
        configure_script = self.absolute_source_path('configure')
        configure_target = Command(
            action = "Configure %s" % self.name,
            target = Target(self.build, self.build_path('build/Makefile')),
            command = [
                'sh',
                configure_script,
                '--prefix', self.absolute_build_path('install'),
            ],
            working_directory = self.build_path('build'),
            env = {
                'CC': self.compiler_binary,
                'MAKE': self.build.make_program,
            },
        ).target
        install_target = Command(
            action = "Install %s" % self.name,
            target = Target(self.build, self.library_path),
            command = [self.build.make_program, 'install'],
            working_directory = self.build_path('build'),
            inputs = [configure_target]
        ).target
        return [install_target]

    @property
    def libraries(self):
        if self.__libraries is not None:
            return self.__libraries
        self.__libraries =  [
            Library(
                self.name,
                self.compiler,
                shared = self.shared,
                search_binary_files = False,
                include_directories = [
                    self.absolute_build_path('install/include/SDL2')
                ],
                directories = [self.absolute_library_directory],
                files = [self.absolute_library_path],
                save_env_vars = False,
            )
        ]
        return self.__libraries

class SDLImageDependency(_Dependency):
    def __init__(self, build, compiler, source_directory, sdl, shared = True):
        super().__init__(build, "SDL_image", source_directory)
        self.shared = shared
        self.compiler = compiler
        ext = self.compiler.library_extension(shared)
        if platform.IS_WINDOWS:
            prefix = ''
        else:
            prefix = 'lib'
        self.library_filename = '%sSDL2_image.%s' % (prefix, ext)
        self.__sdl = sdl
        self.__libraries = None

    def _targets(self):
        configure_script = self.absolute_source_path('configure')
        configure_target = Command(
            action = "Configure %s" % self.name,
            target = Target(self.build, self.build_path('build/Makefile')),
            command = [
                'sh',
                configure_script,
                '--prefix', self.absolute_build_path('install'),
                '--with-sdl-prefix=%s' % self.__sdl.absolute_install_directory,
                '--disable-sdltest',
                '--disable-webp',
                '--enable-fast-install',
                '--disable-dependency-tracking',
                '--disable-silent-rules',
                '--with-pic',
            ],
            working_directory = self.build_path('build'),
            env = {
                'CC': self.compiler_binary,
                'MAKE': self.compiler.build.make_program,
            },
            inputs = self.__sdl.targets,
        ).target
        install_target = Command(
            action = "Install %s" % self.name,
            target = Target(self.build, self.library_path),
            command = [self.build.make_program, 'install'],
            working_directory = self.build_path('build'),
            inputs = [configure_target],
        ).target
        return [install_target]

    @property
    def libraries(self):
        if self.__libraries is not None:
            return self.__libraries
        self.__libraries =  [
            Library(
                self.name,
                self.compiler,
                shared = self.shared,
                search_binary_files = False,
                include_directories = [
                    self.absolute_build_path('install/include/SDL2')
                ],
                directories = [self.absolute_library_directory],
                files = [self.absolute_library_path],
                save_env_vars = False,
            )
        ]
        return self.__libraries
