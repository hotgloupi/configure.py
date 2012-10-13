# -*- encoding: utf-8 -*-

from tupcfg import Target
from . import compiler

            #from os.path import dirname, abspath
            #closure = set()
            #def add_rpath(lib, **kw):
            #    p = '-Wl,-rpath=\\$ORIGIN/' + dirname(lib.relpath(kw['target'], **kw))
            #    if p in closure:
            #        return ''
            #    else:
            #        closure.add(p)
            #        return p
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

    def __get_link_flags(self, cmd, **kw):
        library_directories = set(self.library_directories)
        link_flags = []
        for lib in cmd.libraries:
            if isinstance(lib, Target):
                #self.linker_flags.append(self.LinkFlag(lib, add_rpath)) #XXX
                link_flags.append(lib)
            else:
                for dir_ in lib.directories:
                    library_directories.add(dir_)
                for name in lib.names:
                    link_flags.append('-l%s' % name)
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
            '-o', kw['target'],
            self.__get_link_flags(cmd, **kw)
        ]
