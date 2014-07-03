# -*- encoding: utf-8 -*-

from ..library import Library
from configure import platform, path, tools
from configure import Dependency, Target
from configure.command import Command

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

        self.libraries = [self] + self.components

from configure.dependency.cmake import CMakeDependency

class SDLDependency(CMakeDependency):
    def __init__(self,
                 build,
                 compiler,
                 source_directory,
                 shared = True,
                 directx = False,
                 atomic = True,
                 audio = True,
                 cpuinfo = True,
                 dlopen = True,
                 events = True,
                 file = True,
                 filesystem = True,
                 haptic = True,
                 joystick = True,
                 loadso = True,
                 power = True,
                 render = True,
                 threads = True,
                 timers = True,
                 video = True):
        if platform.IS_MACOSX and shared:
            name = 'SDL2-2.0'
        else:
            name = 'SDL2'

        super().__init__(
            build,
            'SDL',
            compiler,
            source_directory,
            libraries = [
                {
                    'name': name,
                    'prefix': compiler.name != 'msvc' and 'lib' or '',
                    'shared': shared,
                    'source_include_directories': ['include'],
                    'directory': compiler.name == 'msvc' and 'bin' or 'lib',
                    'imp_directory': 'lib',
                }
            ],
            configure_variables = [
                ('DIRECTX', directx),
                ('SDL_SHARED', shared),
                ('SDL_STATIC', not shared),
                ('RPATH', True),
                ('SDL_AUDIO', audio),
                ('SDL_ATOMIC', atomic),
                ('SDL_CPUINFO', cpuinfo),
                ('SDL_DLOPEN', dlopen),
                ('SDL_EVENTS', events),
                ('SDL_FILE', file),
                ('SDL_FILESYSTEM', filesystem),
                ('SDL_HAPTIC', haptic),
                ('SDL_JOYSTICK', joystick),
                ('SDL_LOADSO', loadso),
                ('SDL_POWER', power),
                ('SDL_RENDER', render),
                ('SDL_THREADS', threads),
                ('SDL_TIMERS', timers),
                ('SDL_VIDEO', video),
            ]
        )

class SDLImageDependency(Dependency):
    def __init__(self,
                 build,
                 compiler,
                 source_directory,
                 sdl,
                 png = None,
                 jpeg = None,
                 shared = True):
        super().__init__(build, "SDL_image", source_directory)
        sources = [
            s for s in tools.glob(self.source_path('*.c'))
        ]
        defines = [
            'LOAD_BMP',
            'LOAD_GIF',
            #'LOAD_JPG',
            #'LOAD_JPG_DYNAMIC',
            'LOAD_LBM',
            'LOAD_PCX',
            #'LOAD_PNG',
            #'LOAD_PNG_DYNAMIC',
            'LOAD_PNM',
            'LOAD_TGA',
            #'LOAD_TIF',
            #'LOAD_TIF_DYNAMIC',
            #'LOAD_WEBP',
            #'LOAD_WEBP_DYNAMIC',
            'LOAD_XCF',
            'LOAD_XPM',
            'LOAD_XV',
            'LOAD_XXX',
            'SDL_IMAGE_USE_COMMON_BACKEND', # XXX should use IMG_ImageIO.m on OS X.
        ]
        include_directories = [self.absolute_source_path()]
        libraries = sdl.libraries
        self.lib = compiler.link_library(
            'SDL_image',
            sources = sources,
            directory = self.build_path('install/lib'),
            include_directories = include_directories,
            shared = shared,
            build = build,
            position_independent_code = True,
            defines = defines,
            libraries = libraries,
        )
        self.shared = shared
        self.targets = [self.lib]

        self.libraries = [
            Library(
                self.name,
                compiler,
                shared = shared,
                search_binary_files = False,
                include_directories = include_directories,
                directories = [self.lib.dirname],
                files = [self.lib.path],
                save_env_vars = False,
            )
        ]

