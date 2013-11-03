# -*- encoding: utf-8 -*-

from ..library import Library
from tupcfg import platform, path, tools
from tupcfg import Dependency, Target
from tupcfg.command import Shell as ShellCommand

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


class SDLDependency(Dependency):
    def __init__(self, compiler, source_directory, shared = True):
        super().__init__("SDL Library", "SDL")
        self.source_directory = source_directory
        self.shared = shared
        self.compiler = compiler
        ext = self.compiler.library_extension(shared)
        if platform.IS_WINDOWS:
            prefix = ''
        else:
            prefix = 'lib'
        self.library_filename = '%sSDL2.%s' % (prefix, ext)
        self.__libraries = None

    @property
    def targets(self):
        configure_script = path.absolute(self.source_directory, 'configure')
        configure_target = Target(
            self.build_path('build/Makefile'),
            ShellCommand(
                "Configure libSDL",
                [
                    configure_script,
                    '--prefix', self.build_path('install', abs=True),
                ],
                working_directory = self.build_path('build'),
                #env = {
                #    'CC': self.compiler.binary,
                #},
            )
        )
        install_target = Target(
            self.library_path,
            ShellCommand(
                "Installing %s" % self.name,
                [self.resolved_build.make_program, 'install'],
                working_directory = self.build_path('build'),
                dependencies = [configure_target]
            )
        )
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
                    self.build_path('install/include/SDL2', abs = True)
                ],
                directories = [self.library_directory],
                files = [self.library_path],
                save_env_vars = False,
            )
        ]
        return self.__libraries

    @property
    def install_directory(self):
        return self.build_path('install', abs = True)

    @property
    def library_directory(self):
        if self.shared and platform.IS_WINDOWS:
            return self.build_path('install/bin', abs = True)
        else:
            return self.build_path('install/lib', abs = True)

    @property
    def library_path(self):
        if self.shared and platform.IS_WINDOWS:
            return self.build_path('install/bin', self.library_filename, abs = True)
        else:
            return self.build_path('install/lib', self.library_filename, abs = True)

class SDLImageDependency(Dependency):
    def __init__(self, compiler, source_directory, sdl, shared = True):
        super().__init__("SDL_image Library", "SDL_image")
        self.source_directory = source_directory
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

    @property
    def targets(self):
        if platform.IS_WINDOWS and tools.which('make') is None:
            raise Exception("SDL_image cannot install properly without a make program available :/")
        configure_script = path.absolute(self.source_directory, 'configure')
        configure_target = Target(
            self.build_path('build/Makefile'),
            ShellCommand(
                "Configure libSDL_image",
                [
                    configure_script,
                    '--prefix', self.build_path('install', abs=True),
                    '--with-sdl-prefix=%s' % self.__sdl.install_directory,
                    '--disable-sdltest',
                ],
                working_directory = self.build_path('build'),
            #    env = {
                    #'CC': self.compiler.binary,
                    # on windows, passing MAKE env var generate errorneous makefiles...
                    #'MAKE': path.basename(self.compiler.build.make_program),
             #   },
                dependencies = self.__sdl.targets,
            )
        )
        install_target = Target(
            self.library_path,
            ShellCommand(
                "Installing %s" % self.name,
                [self.resolved_build.make_program, 'install'],
                working_directory = self.build_path('build'),
                dependencies = [configure_target],
            )
        )
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
                    self.build_path('install/include/SDL2', abs = True)
                ],
                directories = [self.library_directory],
                files = [self.library_path],
                save_env_vars = False,
            )
        ]
        return self.__libraries


    @property
    def install_directory(self):
        return self.build_path('install', abs = True)

    @property
    def library_directory(self):
        if self.shared and platform.IS_WINDOWS:
            return self.build_path('install/bin', abs = True)
        else:
            return self.build_path('install/lib', abs = True)

    @property
    def library_path(self):
        if self.shared and platform.IS_WINDOWS:
            return self.build_path('install/bin', self.library_filename, abs = True)
        else:
            return self.build_path('install/lib', self.library_filename, abs = True)
