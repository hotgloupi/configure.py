# -*- encoding: utf-8 -*-

from tupcfg import Target, path
from . import compiler

class LinkFlag:
    def __init__(self, lib, method):
        self.lib = lib
        self.method = method

    def shell_string(self, **kw):
        return self.method(self.lib, **kw)


class Compiler(compiler.Compiler):

    binary_name = 'g++'

    __standards_map = {
        'c++11': 'c++11',
    }

    def __get_build_flags(self, cmd, **kw):
        flags = ['-x', 'c++']
        pic = kw.get('position_independent_code',
                     self.position_independent_code)
        if pic:
            flags.append('-fPIC')
        std = kw.get('standard', self.standard)
        if std:
            flags.append('-std=%s' % self.__standards_map[std])
        include_directories = set(self.include_directories)
        for lib in cmd.libraries:
            if isinstance(lib, Target):
                continue
            for dir_ in lib.include_directories:
                include_directories.add(dir_)
        return flags + list(('-I%s' % i) for i in include_directories)

    def _build_object_cmd(self, cmd, **kw):
        assert len(cmd.dependencies) == 1
        return [
            self.binary,
            self.__get_build_flags(cmd, **kw),
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
        for lib in cmd.libraries:
            if isinstance(lib, Target):
                link_flags.append(lib)
                rpath.libs.append(lib)
            else:
                for dir_ in lib.directories:
                    library_directories.add(dir_)
                for name in lib.names:
                    link_flags.append('-l%s' % name)
        rpath.directories.extend(library_directories)
        link_flags.append(rpath)
        return list(('-L%s' % l) for l in library_directories) + link_flags

    def _link_executable_cmd(self, cmd, **kw):
        return [
            self.binary,
            cmd.dependencies,
            '-o', kw['target'],
            self.__get_link_flags(cmd, **kw)
        ]

    def _link_library_cmd(self, cmd, **kw):
        return [
            self.binary,
            cmd.dependencies,
            cmd.shared and '-shared' or '',
            cmd.shared and '-Wl,-soname,' + path.basename(kw['target'].path(**kw)),
            '-o', kw['target'],
            self.__get_link_flags(cmd, **kw)
        ]
