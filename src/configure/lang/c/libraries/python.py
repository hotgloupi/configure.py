# -*- encoding: utf-8 -*-

import os

from ..library import Library
from configure import path

from sysconfig import get_config_var as var

from configure import path, platform, Dependency, Target
from configure.command import Command

class PythonLibrary(Library):
    def __init__(self, compiler,
                 preferred_shared=True,
                 executable=None,
                 **kw):
        include_dir = var('INCLUDEPY')
        assert include_dir is not None
        prefix = path.clean(var('prefix'))
        assert prefix is not None

        directories = []
        if var('LIBPL'):
            directories.append(path.clean(var('LIBPL')))
        if var('base'):
            directories.append(path.join(var('base'), 'libs'))
            directories.append(path.join(var('base'), 'DLLs'))
        self.version = (var('py_version')[0], var('py_version')[2])
        name_suffixes = [''.join(self.version), '']
        for k in ['LDVERSION', 'py_version_nodot', 'py_version_short']:
            if var(k):
                name_suffixes.append(var(k))

        super().__init__(
            "python",
            compiler,
            find_includes = ['Python.h'],
            name_suffixes = name_suffixes,
            prefixes = [prefix],
            include_directories = var('INCLUDEPY') and [var('INCLUDEPY')] or [],
            directories = directories,
            preferred_shared = preferred_shared,
            shared = kw.get('shared'),
        )
        components = []
        if platform.IS_WINDOWS and not self.shared:
            components = ['pyexpat', 'unicodedata']
        self.components = list(
            Library(
                component,
                compiler,
                prefixes = [prefix],
                include_directories = var('INCLUDEPY') and [var('INCLUDEPY')] or [],
                directories = directories,
                shared = self.shared,
            ) for component in components
        )

        self.ext = var('SO')[1:]

        self.libraries = [self] + self.components


class PythonDependency(Dependency):

    def __init__(self,
                 build,
                 c_compiler,
                 source_directory,
                 shared = True,
                 build_config = [],
                 version: "A tuble of (major, minor)" = None,
                 with_valgrind_support: "Compile with valgrind support" = False,
                 debug: "Compile with Py_DEBUG defined" = False,
                 pymalloc: "Compile with py_malloc" = False,
                 wide_unicode: "Compile with wide unicode" = True):

        build_config = build_config + [
            c_compiler.name,
            debug and 'debug' or 'release',
        ]
        if not pymalloc:
            build_config.append('no-pymalloc')
        if not wide_unicode:
            build_config.append('no-wide-unicode')
        super().__init__(
            build,
            name = "Python%s%s" % version,
            source_directory = source_directory,
            build_config = build_config,
        )
        if c_compiler.lang != 'c':
            raise Exception(
                "%s needs a C compiler, got %s" % (self.name, c_compiler)
            )

        self.compiler = c_compiler
        self.shared = shared
        self.version = version
        self.with_valgrind_support = with_valgrind_support
        self.debug = debug
        self.pymalloc = pymalloc
        self.wide_unicode = wide_unicode
        library_ext = self.compiler.library_extension(shared)
        self.library_filename = 'libpython%s.%s%s.%s' % (
            version + (self.suffix, library_ext,)
        )
        self.interpreter_path = self.absolute_build_path(
            'install/bin/python%s.%s%s' % (version + (self.suffix,)),
        )
        self.prefix_directory = self.absolute_build_path('install')
        self.__targets = None

        self.libraries =  [
            Library(
                self.name,
                self.compiler,
                shared = self.shared,
                search_binary_files = False,
                include_directories = [
                    self.absolute_build_path(
                        'install/include/python%s.%s%s' % (self.version + (self.suffix,)),
                    )
                ],
                directories = [self.absolute_build_path('install/lib')],
                files = [self.absolute_build_path('install/lib', self.library_filename)],
                save_env_vars = False,
            )
        ]

    @property
    def ext(self):
        return  'so' #XXX wrong extension

    @property
    def suffix(self):
        return ''.join([
            self.debug and 'd' or '',
            self.pymalloc and 'm' or '',
           # self.wide_unicode and 'u' or '', #XXX
        ])

    @property
    def targets(self):
        if self.__targets is not None:
            return self.__targets
        configure_args = [
            '--prefix', self.absolute_build_path('install'),
            '--without-suffix',
        ]
        if self.shared:
            configure_args.append('--enable-shared')
        if self.with_valgrind_support:
            configure_args.append('--with-valgrind')
        bool_with = lambda b: b and 'with' or 'without'
        configure_args.extend([
            '--%s-pydebug' % bool_with(self.debug),
            '--%s-pymalloc' % bool_with(self.pymalloc),
            #'--%s-wide-unicode' % bool_with(self.wide_unicode), #XXX version?
        ])

        configure_script = self.absolute_source_path('configure')
        configure_target = Command(
            action = "Configuring %s" % self.name,
            target = Target(self.build, self.build_path('build/Makefile')),
            command = [configure_script] + configure_args,
            env = {'CC': self.compiler.binary},
            working_directory = self.absolute_build_path('build')
        ).target

        install_target = Command(
            action = "Installing %s" % self.name,
            target = Target(self.build, self.build_path('install/lib', self.library_filename)),
            command = [self.build.make_program, 'install'],
            working_directory = self.absolute_build_path('build'),
            inputs = [configure_target],
            env = {
                'PATH': os.environ['PATH'],
            }
        ).target

        self.__targets = [install_target]
        return self.__targets
