# -*- encoding: utf-8 -*-

from configure import platform
from configure.build import command as build_command

from ..library import Library

class BoostLibrary(Library):
    def __init__(self, compiler, components=[], **kw):
        super().__init__(
            "boost",
            compiler,
            find_includes=['boost/config.hpp'],
            search_binary_files = False,
        )

        self.components = []
        for component in components:
            shared = kw.get('%s_shared' % component, kw.get('shared', True))
            if shared:
                name_prefixes = ['', 'lib']
            else:
                name_prefixes = ['lib']
            name_suffixes = ['', '-mt']
            self.components.append(
                Library(
                    "boost_" + component,
                    compiler,
                    prefixes = self.prefixes,
                    include_directories = self.include_directories,
                    directories = self.directories,
                    shared = shared,
                    name_prefixes = name_prefixes,
                    name_suffixes = name_suffixes,
                )
            )
        self.libraries = self.components

from configure import path, tools, Dependency, Target
from configure.command import Command

class BoostDependency(Dependency):

    # Default options.
    default_options = {
        'python': {
            # static build does not work for multiple modules.
            'shared': True,
        },

        'config': {
        },


        'coroutine': {
            'shared': False,
            'multithreading': True,
        },

        'context': {
            'shared': False,
            'multithreading': True,
        },

        'filesystem': {
            # Dynamic linking causes segfaults with directory iterators on OSX.
            'shared': False,
        },

        'thread': {
            'multithreading': True,
        },

        'system': {

        },
    }

    # Libraries inter dependencies.
    inter_dependencies = {
        'algorithm': ['range'],
        'bind': ['smart_ptr'],
        'chrono': ['ratio', 'mpl', 'system', ],
        'config': ['detail', ],
        'conversion': ['numeric/conversion'],
        'coroutine': ['context', ],
        'date_time': ['chrono', ],
        'detail': ['predef', ],
        'exception': ['units', ],
        'filesystem': [
            'functional',
            'io',
            'range',
            'smart_ptr',
            'system',
            'type_traits',
            'utility',
        ],
        'format': ['array', 'math', 'container', ],
        'function': ['bind', ],
        'iterator': ['static_assert'],
        'mpl': ['preprocessor', ],
        'multi_index': ['foreach', 'serialization', ],
        'python': [
            'conversion',
            'function',
            'graph',
            'mpl',
            'smart_ptr',
            'system',
            'type_traits',
            'utility',
        ],
        'property_map': ['concept_check', ],
        'range': ['concept_check', ],
        'signals2': ['any', 'variant', ],
        'smart_ptr': ['exception', ],
        'system': ['config', 'integer', 'utility', ],
        'thread': [
            'atomic',
            'bind',
            'date_time',
            'function',
            'functional',
            'io',
            'move',
            'optional',
            'system',
            'tuple',
            'type_traits',
        ],
        'timer': ['config', 'chrono', 'type_traits', 'exception'],
        'graph': [
            'unordered',
            'tuple',
            'optional',
            'property_map',
            'typeof',
            'multi_index',
            'parameter',
            'range',
        ],
        'type_traits': ['mpl', ],
        'units': ['algorithm', ],
        'utility': ['iterator'],
        'unordered': ['functional', 'move'],
    }

    def __component_dependencies(self, component):
        def gen(l):
            for e in l:
                yield e
                for dep in gen(self.inter_dependencies.get(e, [])):
                    yield dep
        return tools.unique(gen(self.inter_dependencies.get(component, [])))


    def __init__(self,
                 build,
                 cxx_compiler,
                 source_directory,
                 shared: """
                    Build shared libraries by default when set to True, static
                    libraries when set to False, and will to both when set to
                    None.
                    Note: use <COMPONENT>_shared to force a particular component
                """ = None,
                 preferred_shared: """
                    Final decision when both static and dynamic libraries are
                    available and shared option is None.
                 """ = False,
                 runtime_link: """
                    Set to False to link statically with standard libraries.
                 """ = True,
                 build_config = [],
                 components: "Boost libraries to install (ex: ['threading', 'system'])" = [],
                 version: "A tuble of (major, minor)" = None,
                 debug: "Compile in debug mode" = False,
                 multithreading: "Support for multithreading" = True,
                 python: "Specify the python library" = None,
                 **kw: "specify component options with <COMPONENT>-<OPTION>"
                ):
        if cxx_compiler.lang != 'c++':
            raise Exception("Boost need a C++ compiler (got %s)" % cxx_compiler)
        build_config = build_config + [
            cxx_compiler.name,
            debug and 'debug' or 'release',
        ]
        if python is not None:
            build_config += ['with-python%s.%s' % python.version]
        if version is None or not isinstance(version, tuple) or len(version) != 2:
            raise Exception("Please specify the tuple version. ex: (1, 54)")

        super().__init__(
            build,
            "Boost%s.%s" % version,
            source_directory = source_directory,
            build_config = build_config
        )
        self.compiler = cxx_compiler
        self.project = self.compiler.project
        self.shared = shared
        self.preferred_shared = preferred_shared
        self.runtime_link = runtime_link
        self.version = version
        self.debug = debug
        self.multithreading = multithreading
        self.component_names = components
        self.component_options = dict((k, self.default_options.get(k, {})) for k in components)
        for name in self.component_names:
            for k, v in kw.items():
                if k.split('_')[0] == name:
                    self.component_options[name][k.split('_')[1:]] = v
        self.python = python
        self.__targets = {}
        self.__header_targets = {}
        self.__component_sources = {}
        names = (name for name in self.component_names if not self.is_header_only(name))
        self.libraries = [
            self.component_library(component) for component in names
        ]

    def option(self, component, option, default = None):
        return self.component_options.get(component, {}).get(option, getattr(self, option, default))

    def component_shared(self, component):
        shared = self.option(component, 'shared', self.shared)
        if shared is None:
            shared = self.preferred_shared
        assert isinstance(shared, bool)
        return shared

    def component_library_filename(self, component):
        filename = 'libboost_%s' % component
        filename += '.%s' % self.compiler.library_extension(self.component_shared(component))
        return filename

    def component_library_path(self, component):
        return self.absolute_build_path(
            'install', 'lib', self.component_library_filename(component),
        )

    def component_sources(self, component):
        if component in self.__component_sources:
            return self.__component_sources[component]

        srcs = None
        if component == 'thread':
            srcs = [
                'future.cpp',
            ]
            if not platform.IS_WINDOWS:
                srcs.extend([
                    'pthread/once.cpp',
                    'pthread/once_atomic.cpp',
                    'pthread/thread.cpp',
                ])
            else:
                srcs.extend([
                    'win32/thread.cpp',
                    'win32/tss_dll.cpp',
                    'win32/tss_pe.cpp',
                ])

        elif component == 'coroutine':
            srcs = [
                'exceptions.cpp',
                'detail/coroutine_context.cpp',
                #'detail/segmented_stack_allocator.cpp',
                (
                    platform.IS_WINDOWS and
                    'detail/standard_stack_allocator_windows.cpp' or
                    'detail/standard_stack_allocator_posix.cpp'
                ),
            ]
        elif component == 'context':
            all_srcs = [
                'asm/jump_arm_aapcs_elf_gas.S',
                'asm/jump_arm_aapcs_macho_gas.S',
                'asm/jump_arm_aapcs_pe_armasm.asm',
                'asm/jump_i386_ms_pe_masm.asm',
                'asm/jump_i386_sysv_elf_gas.S',
                'asm/jump_i386_sysv_macho_gas.S',
                'asm/jump_mips32_o32_elf_gas.S',
                'asm/jump_ppc32_sysv_elf_gas.S',
                'asm/jump_ppc64_sysv_elf_gas.S',
                'asm/jump_sparc64_sysv_elf_gas.S',
                'asm/jump_sparc_sysv_elf_gas.S',
                'asm/jump_x86_64_ms_pe_masm.asm',
                'asm/jump_x86_64_sysv_elf_gas.S',
                'asm/jump_x86_64_sysv_macho_gas.S',
                'asm/make_arm_aapcs_elf_gas.S',
                'asm/make_arm_aapcs_macho_gas.S',
                'asm/make_arm_aapcs_pe_armasm.asm',
                'asm/make_i386_ms_pe_masm.asm',
                'asm/make_i386_sysv_elf_gas.S',
                'asm/make_i386_sysv_macho_gas.S',
                'asm/make_mips32_o32_elf_gas.S',
                'asm/make_ppc32_sysv_elf_gas.S',
                'asm/make_ppc64_sysv_elf_gas.S',
                'asm/make_sparc64_sysv_elf_gas.S',
                'asm/make_sparc_sysv_elf_gas.S',
                'asm/make_x86_64_ms_pe_masm.asm',
                'asm/make_x86_64_sysv_elf_gas.S',
                'asm/make_x86_64_sysv_macho_gas.S',
            ]
            if platform.IS_WINDOWS:
                abi = 'ms'
            else:
                abi = 'sysv'
            processor = {
                'i386': 'i386',
                'i686': 'i386',
                'AMD64': 'i386',
                'x86_64': 'x86_64',
            }[platform.PROCESSOR]
            binary_format = platform.BINARY_FORMAT.lower()
            pattern = '_%s_%s_%s' % (processor, abi, binary_format)
            srcs = [s for s in all_srcs if pattern in s]

        if srcs is not None:
            srcs = list(
                path.relative(
                    str(self.absolute_source_path('libs', component, 'src', src)),
                    start = self.project.directory
                ) for src in srcs
            )
        else:
            srcs = list(tools.rglob(
                '*.cpp',
                path.relative(
                    str(self.absolute_source_path('libs', component, 'src')),
                    start = self.project.directory
                )
            ))
        self.__component_sources[component] = srcs
        return srcs

    def is_header_only(self, component):
        return len(self.component_sources(component)) == 0

    class lazy_arg:
        def __init__(self, name, arg):
            self.name = name
            self.arg = arg
        def __str__(self):
            return self.name % self.arg

    @property
    def targets(self):
        res = [
            self._target(name) for name in self.component_names
            if not self.is_header_only(name)
        ]
        return res

    def _header_targets(self, name):
        if name not in self.__header_targets:
            include_dir = str(
                self.absolute_source_path('libs', name, 'include')
            )
            res = []
            for pat in ['*.h', '*.[hi]pp']:
                for h in tools.rglob(pat, include_dir):
                    res.append(self.build.fs.copy(
                        h,
                        dest = str(self.build_path(
                            'install',
                            'include',
                            path.relative(h, start = include_dir)
                        ))
                    ))
            self.__header_targets[name] = res
        return self.__header_targets[name]

    @property
    def root_directory(self):
        return self.absolute_build_path('install')

    @property
    def include_directory(self):
        return self.absolute_source_path()

    @property
    def library_directory(self):
        return self.absolute_build_path('install', 'lib')

    def _target(self, name):
        if name in self.__targets:
            return self.__targets[name]
        libraries = []
        dependencies = []
        if name == 'python' and self.python:
            libraries.extend(self.python.libraries)
            dependencies.extend(self.python.targets)
        component_dependencies = self.__component_dependencies(name)
        target = self.__targets[name] = self.compiler.link_library(
            'libboost_' + name,
            directory = self.build_path('install/lib'),
            shared = self.component_shared(name),
            sources = self.component_sources(name),
            include_directories = [
                #when headers are copyied
                #str(self.build_path('install', 'include', abs = True)),
                str(self.source_path()),
            ],
            force_includes = ['cmath'],
            libraries = libraries,
            build = self.build,
            defines = [
                'BOOST_%s_SOURCE' % name.upper(),
                'BOOST_%s_%s_LINK' % (
                    name.upper(),
                    self.component_shared(name) and 'DYN' or 'STATIC'
                ),
                'BOOST_%s_BUILD_%s' % (
                    name.upper(),
                    self.component_shared(name) and 'DLL' or 'LIB'
                ),
            ],
        )
        for dep in dependencies:
            target.dependencies.insert(0, dep)
        return target

    def component_library(self, component):
        return Library(
            self.name + '-' + component,
            self.compiler,
            shared = self.component_shared(component),
            search_binary_files = False,
            include_directories = [
                #self.build_path('install', 'include', abs = True)
                self.include_directory
            ],
            directories = [self.absolute_build_path('install/lib')],
            files = [self.component_library_path(component)],
            save_env_vars = False,
        )

    #@property
    #def targets(self):
    #    if self.__targets is not None:
    #        return list(self.__targets.values())

    #    bootstrap_script = self.source_path('bootstrap.sh')
    #    b2_target = Target(
    #        self.source_path('b2'),
    #        ShellCommand(
    #            "Bootstrap %s" % self.name,
    #            [bootstrap_script],
    #            env = {'CXX': self.compiler.binary},
    #            working_directory = self.source_path()
    #        ),
    #    )
    #    class JamConf:
    #        def __init__(self, compiler, python,
    #                     prefix = None,
    #                     exec_prefix = "bin",
    #                     library_directory = "lib",
    #                     include_directory = "include"):
    #            assert prefix is not None #########
    #            self.prefix = prefix ###############
    #            self.compiler = compiler ############
    #            self.python = python #################
    #            self.exec_prefix = exec_prefix ########
    #            self.library_directory = library_directory
    #            self.include_directory = include_directory

    #        def __call__(self, **kw):
    #            # XXX use shell strings
    #            eval = lambda n: build_command([n], build = kw['build'])[0]
    #            prefix = path.absolute(eval(self.prefix))
    #            exec_prefix = path.join(prefix, eval(self.exec_prefix))
    #            library_directory = path.join(prefix, eval(self.library_directory))
    #            include_directory = path.join(prefix, eval(self.include_directory))
    #            stdlib_flag = (
    #                self.compiler.stdlib is False and "-nostdlib" or (
    #                    isinstance(self.compiler.stdlib, str) and
    #                    "-stdlib=%s" % self.compiler.stdlib or ""
    #                )
    #            )
    #            flags =  ' '.join([
    #                '-std=%s' % self.compiler.standard,
    #                platform.IS_MACOSX and '-headerpad_max_install_names' or '',
    #            ])
    #            return '\n\n'.join((
    #                "import toolset : using ;",
    #                "import option ;",
    #                "import feature ;",
    #                (
    #                    "using %(toolset)s\n"
    #                    " : \n"
    #                    " : %(binary)s ;\n"
    #                ) % {
    #                    'toolset': self.compiler.name,
    #                    'binary': self.compiler.binary,
    #                },
    #                #"flags darwin.compile OPTIONS : -gdwarf-2 ;",
    #                "using python\n : %s\n : %s\n : %s\n : %s ;" % (
    #                    '%s.%s' % self.python.version,
    #                    self.python.interpreter_path,
    #                    self.python.libraries[0].include_directories[0],
    #                    self.python.libraries[0].directories[0],
    #                ),
    #                "option.set prefix : %s ;" % prefix,
    #                "option.set exec-prefix : %s ;" % exec_prefix,
    #                "option.set libdir : %s ;" % library_directory,
    #                "option.set includedir : %s ;" % include_directory,
    #            ))

    #    project_config = self.compiler.build.fs.generate(
    #        self.source_path('project-config.jam'),
    #        JamConf(self.compiler, self.python, prefix = self.build_path('install'))
    #    )

    #    # Include library dependencies
    #    component_names = set(
    #        sum((self.inter_dependencies.get(name, []) for name in self.component_names), [])
    #        + self.component_names
    #    )

    #    # Sort them by dependency
    #    def get_depth(name):
    #        def _find(name, dep, lvl):
    #            if name == dep:
    #                return lvl
    #            return min(list(
    #                _find(name, d, lvl - 1)
    #                for d in self.inter_dependencies.get(name, [name])
    #                if d != dep
    #            ) or [0])
    #        return min(
    #            _find(name, dep, 0) for dep in self.inter_dependencies.keys()
    #        )
    #    component_names = list(sorted(component_names, key = get_depth))


    #    self.__targets = {}
    #    for component in component_names:
    #        self.__targets[component] = self._target(
    #            component,
    #            [b2_target] + self.python.targets + [project_config]
    #        )
    #    return list(self.__targets.values())

    #def _target(self, component, dependencies):
    #    shared = self.component_shared(component)
    #    shared_arg = {
    #        True: 'shared',
    #        False: 'static',
    #    }[shared]
    #    multithreading = self.option(component, 'multithreading')
    #    multithreading_arg = multithreading and 'multi' or 'single'

    #    runtime_link = self.option(component, 'runtime_link')
    #    runtime_link_arg = runtime_link and 'shared' or 'static'

    #    include_directories = self.compiler.include_directories[:]
    #    library_directories = self.compiler.library_directories[:]
    #    for l in self.compiler.libraries:
    #        include_directories.extend(l.include_directories)
    #        library_directories.extend(l.directories)
    #    build_args = [
    #        self.lazy_arg('--build-dir=%s', self.build_path('build')),
    #        self.lazy_arg('--prefix=%s', self.build_path('install', abs = True)),
    #        '--layout=tagged',
    #        '--reconfigure',
    #        '--debug-configuration',
    #        #'--debug-building',
    #        '-o', 'build_test.log',
    #        'toolset=%s' % self.compiler.name,
    #        'variant=%s' % (self.debug and 'debug' or 'release'),
    #        'link=%s' % shared_arg,
    #        'threading=%s' % multithreading_arg,
    #        'runtime-link=%s' % runtime_link_arg,
    #        'include=%s' % ' '.join(map(str, include_directories)),
    #        # XXX define =
    #        'cxxflags=-std=c++11 -stdlib=libc++ %s' % ' '.join(
    #            '-isystem %s' % i for i in include_directories
    #        ),
    #        'linkflags=-stdlib=libc++ %s -lc++' % ' '.join(
    #            '-L %s' % i for i in library_directories
    #        ),
    #    ]

    #    fixup_commands = []
    #    if platform.IS_MACOSX and self.component_shared(component):
    #        def change_install_name(of, in_):
    #            filename = self.component_library_filename(of)
    #            libpath = self.component_library_path(in_)
    #            return ShellCommand(
    #                "Link with a relative install name of %s" % of,
    #                [
    #                    'install_name_tool',
    #                    '-change',
    #                    filename,
    #                    '@rpath/%s' % filename,
    #                    libpath,
    #                ]
    #            )
    #        fixup_commands.extend(
    #            change_install_name(dep, component)
    #            for dep in self.inter_dependencies.get(component, [])
    #            if self.component_shared(dep)
    #        )
    #        filename = self.component_library_filename(component)
    #        libpath = self.component_library_path(component)
    #        fixup_commands.append(
    #            ShellCommand(
    #                "Set a relative install name",
    #                [
    #                    'install_name_tool',
    #                    '-id', '@rpath/%s' % filename,
    #                    libpath,
    #                ]
    #            )
    #        )

    #    filename = self.component_library_filename(component)
    #    libpath = self.component_library_path(component)

    #    return Target(
    #        libpath,
    #        [
    #            ShellCommand(
    #                "Build %s" % self.name,
    #                [self.source_path('b2')] + build_args + [
    #                    '--with-%s' % component,
    #                    'release', 'install',
    #                ],
    #                env = {'CXX': self.compiler.binary},
    #                working_directory = self.source_path(),
    #                # We know that all dependencies will be in self.__targets
    #                # because of the sort above
    #                dependencies = dependencies + [
    #                    self.__targets[dep]
    #                    for dep in self.inter_dependencies.get(component, [])
    #                ]
    #            ),
    #        ] + fixup_commands
    #    )

    #@property
    #def libraries(self):
    #    if self.__libraries is not None:
    #        return self.__libraries
    #    self.__libraries = [
    #        Library(
    #            self.name + '-' + component,
    #            self.compiler,
    #            shared = self.component_shared(component),
    #            search_binary_files = False,
    #            include_directories = [
    #                self.build_path(
    #                    'install/include',
    #                    abs = True
    #                )
    #            ],
    #            directories = [self.build_path('install/lib', abs = True)],
    #            files = [self.component_library_path(component)],
    #            save_env_vars = False,
    #        ) for component in self.component_names
    #    ]
    #    return self.__libraries
