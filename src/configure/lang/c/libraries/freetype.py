# -*- encoding: utf-8 -*-

from ..library import Library

from configure import path, platform, Dependency, Target
from configure.command import Command

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
                 build,
                 c_compiler,
                 source_directory,
                 shared = False,
                 build_config = []):
        super().__init__(
            build,
            name = "Freetype2",
            source_directory = source_directory,
            build_config = build_config or [c_compiler.name, ],
        )
        if c_compiler.lang != 'c':
            raise Exception(
                "Freetype needs a C compiler, got %s" % c_compiler
            )
        self.compiler = c_compiler
        self.shared = shared
        ext = self.compiler.library_extension(shared)
        self.library_filename = 'libfreetype.%s' % ext
        self.env = {'CC': c_compiler.binary}
        sources = [
            "src/base/ftsystem.c", #
            "src/base/ftinit.c", #
            "src/base/ftdebug.c", #
            "src/base/ftbase.c", #
            "src/base/ftbbox.c", #       -- recommended, see <freetype/ftbbox.h>
            "src/base/ftglyph.c", #      -- recommended, see <freetype/ftglyph.h>
            "src/base/ftbdf.c", #        -- optional, see <freetype/ftbdf.h>
            "src/base/ftbitmap.c", #     -- optional, see <freetype/ftbitmap.h>
            "src/base/ftcid.c", #        -- optional, see <freetype/ftcid.h>
            "src/base/ftfstype.c", #     -- optional
            "src/base/ftgasp.c", #       -- optional, see <freetype/ftgasp.h>
            "src/base/ftgxval.c", #      -- optional, see <freetype/ftgxval.h>
            "src/base/ftlcdfil.c", #     -- optional, see <freetype/ftlcdfil.h>
            "src/base/ftmm.c", #         -- optional, see <freetype/ftmm.h>
            "src/base/ftotval.c", #      -- optional, see <freetype/ftotval.h>
            "src/base/ftpatent.c", #     -- optional
            "src/base/ftpfr.c", #        -- optional, see <freetype/ftpfr.h>
            "src/base/ftstroke.c", #     -- optional, see <freetype/ftstroke.h>
            "src/base/ftsynth.c", #      -- optional, see <freetype/ftsynth.h>
            "src/base/fttype1.c", #      -- optional, see <freetype/t1tables.h>
            "src/base/ftwinfnt.c", #     -- optional, see <freetype/ftwinfnt.h>
            "src/base/ftxf86.c", #       -- optional, see <freetype/ftxf86.h>

            "src/bdf/bdf.c", #           -- BDF font driver
            "src/cff/cff.c", #           -- CFF/OpenType font driver
            "src/cid/type1cid.c", #      -- Type 1 CID-keyed font driver
            "src/pcf/pcf.c", #           -- PCF font driver
            "src/pfr/pfr.c", #           -- PFR/TrueDoc font driver
            "src/sfnt/sfnt.c", #         -- SFNT files support (TrueType & OpenType)
            "src/truetype/truetype.c", # -- TrueType font driver
            "src/type1/type1.c", #       -- Type 1 font driver
            "src/type42/type42.c", #     -- Type 42 font driver
            "src/winfonts/winfnt.c", #   -- Windows FONT / FNT font driver

            "src/raster/raster.c", #     -- monochrome rasterizer
            "src/smooth/smooth.c", #     -- anti-aliasing rasterizer

            "src/autofit/autofit.c", #   -- auto hinting module
            "src/cache/ftcache.c", #     -- cache sub-system (in beta)
            "src/gzip/ftgzip.c", #       -- support for compressed fonts (.gz)
            "src/lzw/ftlzw.c", #         -- support for compressed fonts (.Z)
            "src/bzip2/ftbzip2.c", #     -- support for compressed fonts (.bz2)
            "src/gxvalid/gxvalid.c", #   -- TrueTypeGX/AAT table validation
            "src/otvalid/otvalid.c", #   -- OpenType table validation
            "src/psaux/psaux.c", #       -- PostScript Type 1 parsing
            "src/pshinter/pshinter.c", # -- PS hinting module
            "src/psnames/psnames.c", #   -- PostScript glyph names support
        ]

        if platform.IS_MACOSX:
            sources.append(
                "src/base/ftmac.c" #        -- only on the Macintosh
            )
        self.__sources = [
            path.relative(
                self.source_path(s),
                start = self.compiler.project.directory
            ) for s in sources
        ]
        self.__targets = None
        self.libraries = [
            Library(
                'freetype2',
                self.compiler,
                shared = self.shared,
                search_binary_files = False,
                include_directories = [
                    self.absolute_source_path('include')
                ],
                directories = [self.absolute_build_path('install/lib')],
                files = [self.absolute_build_path('install/lib', self.library_filename)],
                save_env_vars = False,
            )
        ]

    @property
    def targets(self):
        if self.__targets is None:
            self.__targets = [
                self.compiler.link_library(
                    'libfreetype',
                    directory = self.build_path('install/lib'),
                    shared = self.shared,
                    defines = ['FT2_BUILD_LIBRARY'],
                    build = self.build,
                    sources = self.__sources,
                    position_independent_code = True,
                    include_directories = [
                        self.source_path('include'),
                    ]
                )
            ]
        return self.__targets


    def old_targets(self):
        copy_target = Target(
            self.build_path('freetype2/autogen.sh'),
            ShellCommand(
                "Copy Freetype2 sources",
                [
                    'cp', '-r', self.source_path(),
                    self.build_path()
                ],
            )
        )

        if platform.IS_WINDOWS:
            configure_target = copy_target
        else:
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
                        './configure', '--prefix', self.absolute_build_path('install')
                    ],
                    working_directory = self.build_path('freetype2'),
                    dependencies = [autogen_target],
                    env = {
                        'CC': self.compiler.binary,
                        'MAKE': self.build.make_program,
                    }
                ),
            )

        build_target = Target(
            self.build_path('install/bin/freetype-config'),
            ShellCommand(
                "Building FreeType2",
                [self.build.make_program],
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

