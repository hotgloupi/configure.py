# -*- encoding: utf-8 -*-

from . import compiler as cxx_compiler
from ..c import gcc
from tupcfg import path

class Compiler(cxx_compiler.Compiler, gcc.Compiler):

    binary_name = 'g++'

    __standards_map = {
        'c++11': 'c++11',
    }

    def __init__(self, project, build, **kw):
        assert self.binary_name == 'g++'
        assert self.binary_env_varname == 'CXX'
        kw.setdefault('lang', 'cxx')
        super(Compiler, self).__init__(project, build, **kw)

    def _get_build_flags(self, cmd):
        base_build_flags =  super(Compiler, self)._get_build_flags(cmd)
        if cmd.kw.get('precompiled_header'):
            lang = 'c++-header'
        else:
            lang = 'c++'
        return (
            ['-x', lang] + base_build_flags +
            self.__get_stdlib_flags(cmd)
        )

    def _get_link_flags(self, cmd):
        flags = super(Compiler, self)._get_link_flags(cmd)
        if self.attr('static_libstd', cmd):
            flags.append('-L%s' % self.static_stdlib_directory)
            flags.append('-static-libstdc++')
        return flags + self.__get_stdlib_flags(cmd)

    def __get_stdlib_flags(self, cmd):
        stdlib = self.attr('stdlib', cmd)
        flags = []
        if not stdlib:
            flags.append('-nostdlib')
        elif isinstance(stdlib, str):
            flags.append('-stdlib=%s' % stdlib)
        return flags

    @property
    def static_stdlib_directory(self):
        if not hasattr(self, '_static_stdlib_directory'):
            import subprocess
            f = subprocess.check_output([self.binary, '--print-file-name=libstdc++.a']).decode('utf8')
            self._static_stdlib_directory = path.dirname(f)
        return self._static_stdlib_directory

