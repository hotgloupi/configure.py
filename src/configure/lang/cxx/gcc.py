# -*- encoding: utf-8 -*-

from . import compiler as cxx_compiler
from ..c import gcc
from configure import path

class Compiler(cxx_compiler.Compiler, gcc.Compiler):

    binary_name = 'g++'

    __standards_map = {
        'c++98': 'c++98',
        'c++03': 'c++03',
        'c++11': 'c++11',
        'c++14': 'c++14',
    }

    def __init__(self, build, **kw):
        kw.setdefault('lang', 'c++')
        kw.setdefault('standard', 'c++11')
        super().__init__(build, **kw)

    def _get_build_flags(self, kw):
        base_build_flags =  super()._get_build_flags(kw)
        if kw.get('precompiled_header'):
            lang = 'c++-header'
        else:
            lang = 'c++'
        return (
            ['-x', lang] + base_build_flags +
            self.__get_stdlib_flags(kw)
        )

    def _get_link_flags(self, kw):
        flags = super()._get_link_flags(kw)
        if self.attr('static_libstd', kw):
            flags.append('-L%s' % self.static_stdlib_directory)
            flags.append('-static-libstdc++')
        return flags + self.__get_stdlib_flags(kw)

    def __get_stdlib_flags(self, kw):
        stdlib = self.attr('stdlib', kw)
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

