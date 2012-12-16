# -*- encoding: utf-8 -*-

import sys
from tupcfg import Target, path, tools, platform
from tupcfg.lang import compiler

class Compiler(compiler.Compiler):

    binary_name = 'gcc'
    ar_binary_name = 'ar'

    __standards_map = {
        'c99': 'c99',
    }

    def __init__(self, project, build, **kw):
        kw.setdefault('lang', 'c')
        super(Compiler, self).__init__(project, build, **kw)
        self.ar_binary = tools.find_binary(self.ar_binary_name, project.env, 'AR')
        project.env.project_set('AR', self.ar_binary)

    def _get_build_flags(self, cmd, **kw):
        flags = []
        pic = self.attr('position_independent_code', cmd, **kw)
        if pic and not platform.IS_WINDOWS:
            flags.append('-fPIC')
        std = self.attr('standard', cmd, **kw)
        if std:
            flags.append('-std=%s' % self.__standards_map[std])

        defines = kw.get('defines', []) + cmd.kw.get('defines', []) + self.defines
        for define in defines:
            if isinstance(define, str):
                flags.append('-D' + define)
            else:
                assert len(define) == 2 #key, value
                flags.append('-D%s=%s' % define)

        return flags + list(
            ('-I%s' % i) for i in self._include_directories(cmd, **kw)
        )

    def _build_object_cmd(self, cmd, **kw):
        assert len(cmd.dependencies) == 1
        return [
            self.binary,
            self.__architecture_flag(cmd, **kw),
            self._get_build_flags(cmd, **kw),
            '-c', cmd.dependencies[0],
            '-o', kw['target'],
        ]

    def __add_rpath(self, lib, **kw):
        return '-Wl,-rpath=\\$ORIGIN/' + path.dirname(lib.relpath(kw['target'], **kw))

    def _get_link_flags(self, cmd, **kw):
        library_directories = set(self.library_directories)
        link_flags = []
        class RPathFlag:
            def __init__(self):
                self.libs = []
                self.directories = []

            def shell_string(self, **kw):
                from os.path import abspath, dirname
                dirs = set(self.directories)
                for lib in self.libs:
                    dirs.add(path.dirname(path.absolute(lib.path(**kw))))
                if dirs:
                    return '-Wl,-rpath,' + ':'.join(dirs)
                return ''

        rpath = RPathFlag()
        for lib in cmd.kw.get('libraries', []):
            if isinstance(lib, Target):
                link_flags.append(lib)
                rpath.libs.append(lib)
            else:
                for dir_ in lib.directories:
                    library_directories.add(dir_)
                for name in lib.names:
                    if not platform.IS_MACOSX:
                        if lib.shared:
                            link_flags.append('-Wl,-Bdynamic')
                        else:
                            link_flags.append('-Wl,-Bstatic')
                    if platform.IS_MACOSX and lib.macosx_framework:
                        link_flags.extend(['-framework', name])
                    else:
                        link_flags.append('-l%s' % name)

        if not platform.IS_MACOSX:
            link_flags.append('-Wl,-Bdynamic')
        rpath.directories.extend(library_directories)
        link_flags.append(rpath)
        return list(('-L%s' % l) for l in library_directories) + link_flags

    def _link_executable_cmd(self, cmd, **kw):
        return [
            self.binary,
            cmd.dependencies,
            self.__architecture_flag(cmd, **kw),
            '-o', kw['target'],
            self._get_link_flags(cmd, **kw)
        ]

    def _link_library_cmd(self, cmd, **kw):
        if cmd.shared:
            if platform.IS_MACOSX:
                link_flag = 'dynamiclib'
                soname_flag = 'dylib_install_name'
            else:
                link_flag = 'shared'
                soname_flag = 'soname'
            return [
                self.binary,
                '-%s' % link_flag,
                self.__architecture_flag(cmd, **kw),
                cmd.dependencies,
                ('-Wl,-%s,' % soname_flag) + path.basename(kw['target'].path(**kw)),
                '-o', kw['target'],
                self._get_link_flags(cmd, **kw)
            ]
        else:
            return [
                self.ar_binary,
                'rcs',
                kw['target'],
                cmd.dependencies,
            ]

    def __architecture_flag(self, cmd, **kw):
        return {
            '64bit': '-m64',
            '32bit': '-m32',
        }[self.attr('architecture', cmd, **kw)]
