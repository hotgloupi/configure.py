# -*- encoding: utf-8 -*-

from ..library import Library

from tupcfg import path, Dependency, Target
from tupcfg.command import Shell as ShellCommand

class FreetypeLibrary(Library):

    def __init__(self, compiler, **kw):
        super().__init__(
            'freetype',
            compiler,
            find_includes = [
                'ft2build.h',
                'freetype/config/ftconfig.h'
            ],
            include_directory_names = ['', 'freetype2'],
            shared = kw.get('shared', True)
        )


class FreetypeDependency(Dependency):
    def __init__(self,
                 c_compiler,
                 source_directory,
                 shared = True,
                 build_config = []):
        super().__init__(
            "Freetype2",
            "freetype2",
            build_config = build_config or [c_compiler.name, ],
        )
        if c_compiler.lang != 'c':
            raise Exception(
                "Freetype needs a C compiler, got %s" % c_compiler
            )
        self.compiler = c_compiler
        self.source_directory = source_directory
        self.shared = shared
        ext = self.compiler.library_extension(shared)
        self.library_filename = 'libfreetype.%s' % ext
        self.env = {'CC': c_compiler.binary}

    @property
    def targets(self):
        copy_target = Target(
            self.build_path('freetype2/autogen.sh'),
            ShellCommand(
                "Copy Freetype2 sources",
                [
                    'cp', '-r', path.absolute(self.source_directory),
                    self.build_path()
                ],
            )
        )

        autogen_target = Target(
            self.build_path('freetype2/configure'),
            ShellCommand(
                "Generating configure script",
                ['./autogen.sh'],
                working_directory = self.build_path('freetype2'),
                dependencies = [copy_target]
            ),
        )

        configure_target = Target(
            self.build_path('freetype2/config.mk'),
            ShellCommand(
                "Configuring Freetype2",
                [
                    './configure', '--prefix', self.build_path('install', abs=True)
                ],
                working_directory = self.build_path('freetype2'),
                dependencies = [autogen_target],
                env = self.env
            ),
        )

        build_target = Target(
            self.build_path('install/bin/freetype-config'),
            ShellCommand(
                "Building FreeType2",
                ['make'],
                working_directory = self.build_path('freetype2'),
                dependencies = [configure_target]
            ),
        )

        install_target = Target(
            self.build_path('install/lib', self.library_filename),
            ShellCommand(
                "Installing FreeType2",
                ['make', 'install'],
                working_directory = self.build_path('freetype2'),
                dependencies = [build_target]
            )
        )
        return [install_target]

    @property
    def libraries(self):
        return [
            Library(
                'freetype2',
                self.compiler,
                shared = self.shared,
                search_binary_files = False,
                include_directories = [
                    self.build_path('install/include/freetype2', abs = True)
                ],
                directories = [self.build_path('install/lib', abs = True)],
                files = [self.build_path('install/lib', self.library_filename, abs = True)],
                save_env_vars = False,
            )
        ]
