# -*- encoding: utf-8 -*-

from tupcfg import path, tools
from tupcfg import Target

from . import compiler as c_compiler

class Compiler(c_compiler.Compiler):

    binary_name = 'cl.exe'
    lib_binary_name = 'lib.exe'
    object_extension = 'obj'

    def __init__(self, project, build, **kw):
        kw.setdefault('lang', 'c')
        super(Compiler, self).__init__(project, build, **kw)
        self.lib_binary = tools.find_binary(self.lib_binary_name, project.env, 'LIBEXE')
        project.env.project_set('LIBEXE', self.lib_binary)

    # Prefix a flag (with '-' or '/')
    def _flag(self, flag):
        return '-' + flag

    def library_extensions(self, shared, for_linker=False):
        if for_linker:
            return ['lib', 'dll']
        if shared:
            return ['dll']
        else:
            return ['lib']

    @property
    def _lang_flag(self):
        return self._flag('Tc')

    def _get_build_flags(self, cmd):
        flags = [
            self._flag('nologo'),   # no print while invoking cl.exe
            self._flag('c'),        # compiles without linking
            self._flag('MD'),
        ]
        if self.attr('enable_warnings', cmd):
            flags += [
                self._flag('W3'),   # warning level (0 -> 4)
                self._flag('WL'),   # Enables one-line diagnostics for error
                                    # and warning messages when compiling C++
                                    # source code from the command line.
            ]
        for dir_ in self._include_directories(cmd):
            flags.extend([
                self._flag('I'),
                dir_,
            ])
        for define in self.attr('defines', cmd):
            if isinstance(define, str):
                flags.extend([self._flag('D'), define])
            else:
                assert len(define) == 2
                key, val = define
                flags.append("%s%s=%s" % (self._flag('D'), key, val))
        return flags

    def _build_object_cmd(self, cmd, target=None, build=None):
        assert len(cmd.dependencies) == 1
        return [
            self.binary,
            self._get_build_flags(cmd),
            self._lang_flag, cmd.dependencies[0],
            self._flag('Fo') + target.path(build),
        ]

    def _link_flags(self, cmd):
        flags = []
        dirs = []
        files = []
        for library in cmd.kw.get('libraries'):
            if isinstance(library, Target):
                continue
            dirs.extend(library.directories)
            files.extend(
                f for f in library.files if not f.endswith('.dll')
            )
        dirs = tools.unique(dirs)
        flags.extend(
            self._flag('LIBPATH') + ':' + dir_ for dir_ in dirs
        )
        flags.extend(
            path.basename(f) for f in files
        )
        flags.append(self.__architecture_flag(cmd))
        return flags


    def _link_library_cmd(self, cmd, target=None, build=None):
        if cmd.shared:
            return [
                self.binary,
                self._flag('nologo'),   # no print while invoking cl.exe
                self._flag('LD'), # dynamic library
                cmd.dependencies,
                self._flag('Fo') + target.path(build),
                self._flag('link'),
                self._link_flags(cmd),
            ]
        else:
            return [
                self.lib_binary,
                cmd.dependencies,
                self._flag('out:') + target.path(build),
                self._link_flags(cmd)
            ]

    def _link_executable_cmd(self, cmd, target=None, build=None):
        return [
            self.binary,
            self._flag('nologo'),   # no print while invoking cl.exe
            cmd.dependencies,
            self._flag('Fo') + target.path(build),
            self._flag('link'),
            self._link_flags(cmd),
        ]

    def __architecture_flag(self, cmd):
        return {
            '64bit': self._flag('MACHINE:')+'x64',
            '32bit': self._flag('MACHINE:')+'x86',
        }[self.attr('architecture', cmd)]
