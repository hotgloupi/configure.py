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
        return ['-x', 'c++'] + super(Compiler, self)._get_build_flags(cmd)

    def _get_link_flags(self, cmd):
        flags = []
        if self.attr('static_libstd', cmd):
            flags.append('-L%s' % self.static_stdlib_directory)
            flags.append('-static-libstdc++')
        return flags + super(Compiler, self)._get_link_flags(cmd)

    @property
    def static_stdlib_directory(self):
        if not hasattr(self, '_static_stdlib_directory'):
            import subprocess
            f = subprocess.check_output([self.binary, '--print-file-name=libstdc++.a']).decode('utf8')
            self._static_stdlib_directory = path.dirname(f)
        return self._static_stdlib_directory

