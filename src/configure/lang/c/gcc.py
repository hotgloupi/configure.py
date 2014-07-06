# -*- encoding: utf-8 -*-

import sys
import pipes

from configure import Target, path, tools, platform
from configure.command import Command

from . import compiler as c_compiler
from . import library

class Compiler(c_compiler.Compiler):

    name = 'gcc'
    binary_name = 'gcc'
    linker_binary_name = 'gcc'
    ar_binary_name = 'ar'
    as_binary_name = 'as'

    # deduced from binary name
    binary = None
    ar_binary = None
    as_binary = None

    __standards_map = {
        'c99': 'c99',
    }

    __warnings_map = {
        'unused-typedefs': 'unused-local-typedefs',
        'unknown-pragmas': 'unknown-pragmas',
        'unused-but-set-parameters': 'unused-but-set-parameters',
        'return-type': 'return-type',
    }

    Library = library.Library

    def __init__(self, build, **kw):
        super().__init__(build, **kw)
        self.ar_binary = self.build.find_binary('ar')
        self.as_binary = self.build.find_binary('as')

    def _get_build_flags(self, kw):
        flags = [
            '-fno-common', # Ensure objects are not shared unless explicitly.
        ]
        pic = self.attr('position_independent_code', kw)
        if pic and not platform.IS_WINDOWS:
            flags.append('-fPIC')
        if self.attr('hidden_visibility', kw):
            flags.append('-fvisibility=hidden')
            flags.append('-fvisibility-inlines-hidden')
        if self.attr('enable_warnings', kw):
            flags.extend(['-Wall', '-Wextra'])

        disabled_warnings = self.list_attr('disabled_warnings', kw)
        for warning in self.disabled_warnings:
            warning_flag = self.__warnings_map.get(warning)
            if warning_flag:
                flags.append('-Wno-' + warning_flag)

        forbidden_warnings = self.list_attr('forbidden_warnings', kw)
        for warning in self.forbidden_warnings:
            warning_flag = self.__warnings_map.get(warning)
            if warning_flag:
                flags.append('-Werror=' + warning_flag)

        optimization = self.attr('optimization', kw)
        if optimization is not None:
            flags.append(
                {
                    self.optimize_size: '-Os',
                    self.dont_optimize: '-O0',
                    self.optimize: '-O1',
                    self.optimize_harder: '-O2',
                    self.optimize_fastest: '-O3',

                }[optimization]
            )
        if self.attr('generate_debug', kw):
            flags.append('-g3')

        std = self.attr('standard', kw)
        if std:
            flags.append('-std=%s' % self.__standards_map[std])

        defines = self.list_attr('defines', kw)
        for define in defines:
            if isinstance(define, str):
                flags.append('-D' + define)
            else:
                assert len(define) == 2 #key, value
                flags.append('-D%s=%s' % define)

        pchs = self.list_attr('precompiled_headers', kw)
        if pchs:
            flags.append('-Winvalid-pch')

        for d in tools.unique(self._include_directories(kw)):
            flags.extend(['-I', d])

        force_includes = self.list_attr('force_includes', kw)
        for i in tools.unique(force_includes):
            flags.extend(['-include', i])
        for pch in pchs:
            flags.extend(['-include', pch.dependencies[0]])

        return flags

    def _build_object_cmd(self, object, source, **kw):
        if source.path.endswith('.S'):
            command = [
                self.as_binary,
                '-o', object,
                source,
            ],
        else:
            command = [
                self.binary,
                self.__architecture_flag(kw),
                self._get_build_flags(kw),
                '-c', source,
                '-o', object,
            ],

        return Command(
            action = kw.get('action', "Build object"),
            command = command,
            target = object,
            inputs = [source],
        )

    def _build_object_dependencies_cmd(self, target, object, source, **kw):
        return Command(
            action = "Build dependencies makefile",
            command = [
                self.binary,
                self.__architecture_flag(kw),
                self._get_build_flags(kw),
                '-c', source,
                '-MM',
                '-MT', object,
                '-MF', target,
            ],
            target = target,
            inputs = [source]
        )

    def __add_rpath(self, lib, **kw):
        return '-Wl,-rpath=\\$ORIGIN/' + path.dirname(lib.relpath(kw['target'], **kw))

    def _get_link_flags(self, kw):
        link_flags = ['-no-canonical-prefixes']
        if self.attr('allow_unresolved_symbols', kw):
            #link_flags.append('-Wl,--allow-shlib-undefined')
            #link_flags.append('-Wl,--unresolved-symbols=ignore-all')
            if self.binary_name in ['clang', 'clang++']: #XXX does not recognize =
                link_flags.extend(['-undefined', 'dynamic_lookup'])
            else:
                link_flags.extend(['-undefined=dynamic_lookup'])
        library_directories = self.library_directories[:]
        pic = self.attr('position_independent_code', kw)
        if pic and not platform.IS_WINDOWS:
            link_flags.append('-fPIC')
        if self.attr('hidden_visibility', kw):
            link_flags.append('-fvisibility=hidden')
            if self.lang == 'c++':
                link_flags.append('-fvisibility-inlines-hidden')

        if platform.IS_MACOSX:
            link_flags.append('-headerpad_max_install_names')
        if platform.IS_WINDOWS:
            link_flags.append('--enable-stdcall-fixup')

        if self.attr('recursive_linking', kw):
            link_flags.append('-Wl,-(')
        rpath_dirs = []
        for lib in self.list_attr('libraries', kw):
            if isinstance(lib, Target):
                link_flags.append(lib)
                rpath_dirs.append(path.dirname(lib.path))
            elif lib.macosx_framework:
                link_flags.extend(['-framework', lib.name])
            elif lib.system == True:
                link_flags.append('-l%s' % lib.name)
            else:
                for f in lib.files:
                    #if not platform.IS_MACOSX:
                    #    if lib.shared:
                    #        link_flags.append('-Wl,-Bdynamic')
                    #    else:
                    #        link_flags.append('-Wl,-Bstatic')
                    link_flags.append(f)
                for dir_ in lib.directories:
                    library_directories.append(dir_)
        if self.attr('recursive_linking', kw):
            link_flags.append('-Wl,-)')

        #if not platform.IS_MACOSX:
        #    link_flags.append('-Wl,-Bdynamic')
        rpath_dirs.extend(library_directories)
        rpath_dirs = tools.unique(path.clean(p) for p in rpath_dirs)
        if rpath_dirs:
            if platform.IS_MACOSX:
                link_flags.extend(('-Wl,-rpath,%s' % d) for d in rpath_dirs)
            elif not platform.IS_WINDOWS:
                link_flags.append('-Wl,-rpath,' + ':'.join(rpath_dirs))
        link_flags.extend(self.additional_link_flags.get(self.name, []))
        if self.attr('static_libstd', kw):
            link_flags.append('-L%s' % self.static_stdlib_directory)
            link_flags.append('-static-libgcc')
        return link_flags

    def _link_executable_cmd(self, target, objects, **kw):
        return Command(
            action = "Link executable",
            command = [
                self.binary,
                objects,
                self.__architecture_flag(kw),
                '-o', target,
                self._get_link_flags(kw)
            ],
            target = target,
            inputs = objects,
            additional_outputs = []
        )

    def _link_library_cmd(self, target, objects, shared = None, **kw):
        assert isinstance(shared, bool)
        additional_outputs = []
        if shared:
            name = target.basename
            if platform.IS_MACOSX:
                link_flag = 'dynamiclib'
                soname_flag = 'install_name'
                name = '@rpath/' + name
            else:
                link_flag = 'shared'
                soname_flag = 'soname'
            shell = [
                self.binary,
                '-%s' % link_flag,
                self.__architecture_flag(kw),
                objects,
                ('-Wl,-%s,' % soname_flag) + name,
                '-o', target,
                self._get_link_flags(kw)
            ]
            if platform.IS_WINDOWS and self.attr('build_import_library', kw):
                implib = Target(
                    target.build,
                    target.relative_path() + '.a',
                    shell_formatter = lambda p: ['-Wl,--out-implib,%s' % p],
                )
                shell.append(implib)
                additional_outputs.append(implib)
        else:
            shell = [
                self.ar_binary,
                'rcs',
                target,
                objects,
            ]
        return Command(
            action = "Link %s library" % (shared and "shared" or "static"),
            command = shell,
            target = target,
            inputs = objects,
            additional_outputs = additional_outputs,
        )

    def __architecture_flag(self, kw):
        if self.force_architecture is False:
            return []
        return {
            '64bit': '-m64',
            '32bit': '-m32',
        }[self.attr('target_architecture', kw)]

    class _LazyUnique:
        def __init__(self, objects, op = None):
            self.objects = objects
            self.op = op
        def shell_string(self, build = None, cwd = None):
            from configure.build import command
            res = tools.unique(
                command(self.objects, build = build, cwd = cwd)
            )
            if self.op is not None:
                return map(self.op, res)
            return res
