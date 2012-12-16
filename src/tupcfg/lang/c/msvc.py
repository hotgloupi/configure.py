# -*- encoding: utf-8 -*-

from tupcfg import tools

from tupcfg.lang import compiler

class Compiler(compiler.Compiler):

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
        return flags

    def _build_object_cmd(self, cmd, target=None, build=None):
        assert len(cmd.dependencies) == 1
        return [
            self.binary,
            self._get_build_flags(cmd),
            self._lang_flag, cmd.dependencies[0],
            self._flag('Fo') + target.path(build),
        ]

    def _link_library_cmd(self, cmd, target=None, build=None):
        if cmd.shared:
            return [
                self.binary,
                self._flag('nologo'),   # no print while invoking cl.exe
                self._flag('LD'), # dynamic library
                cmd.dependencies,
                self._flag('Fo') + target.path(build)
            ]
        else:
            return [
                self.lib_binary,
                cmd.dependencies,
            ]

    def _link_executable_cmd(self, cmd, target=None, build=None):
        return [
            self.binary,
            self._flag('nologo'),   # no print while invoking cl.exe
            cmd.dependencies,
            self._flag('Fo') + target.path(build),
        ]

