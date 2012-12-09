# -*- encoding: utf-8 -*-

import sys
from tupcfg import Target, path, tools, platform
from . import compiler

class LinkFlag:
    def __init__(self, lib, method):
        self.lib = lib
        self.method = method

    def shell_string(self, **kw):
        return self.method(self.lib, **kw)


class Compiler(compiler.Compiler):

    binary_name = 'g++'
    ar_binary_name = 'ar'

    __standards_map = {
        'c++11': 'c++11',
    }

    def __init__(self, project, build, **kw):
        compiler.Compiler.__init__(self, project, build, **kw)
        self.ar_binary = tools.find_binary(self.ar_binary_name, project.env, 'AR')
        project.env.project_set('AR', self.ar_binary)

    def __get_build_flags(self, cmd):
        flags = ['-x', 'c++']
        pic = cmd.kw.get('position_independent_code',
                         self.position_independent_code)
        if pic and sys.platform != 'win32':
            flags.append('-fPIC')
        std = cmd.kw.get('standard', self.standard)
        if std:
            flags.append('-std=%s' % self.__standards_map[std])
        defines = cmd.kw.get('defines', []) + self.defines
        for define in defines:
            if isinstance(define, str):
                flags.append('-D' + define)
            else:
                assert len(define) == 2 #key, value
                flags.append('-D%s=%s' % define)

        include_directories = set(
            self.include_directories +
            cmd.kw.get('include_directories', [])
        )
        libraries = cmd.kw.get('libraries', []) #+ self.libraries
        for lib in libraries:
            if isinstance(lib, Target):
                continue
            for dir_ in lib.include_directories:
                include_directories.add(dir_)
        return flags + list(('-I%s' % i) for i in include_directories)

    def _build_object_cmd(self, cmd, **kw):
        assert len(cmd.dependencies) == 1
        return [
            self.binary,
            self.__architecture_flag(cmd, **kw),
            self.__get_build_flags(cmd),
            '-c', cmd.dependencies[0],
            '-o', kw['target'],
        ]

    def __add_rpath(self, lib, **kw):
        return '-Wl,-rpath=\\$ORIGIN/' + path.dirname(lib.relpath(kw['target'], **kw))

    def __get_link_flags(self, cmd, **kw):
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
            self.__get_link_flags(cmd, **kw)
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
                self.__get_link_flags(cmd, **kw)
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
        }[kw.get('architecture', self.architecture)]
