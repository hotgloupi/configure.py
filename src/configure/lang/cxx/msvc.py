#-*- encoding: utf8 -*-

from . import compiler as cxx_compiler
from ..c import msvc

class Compiler(cxx_compiler.Compiler, msvc.Compiler):

    def __init__(self, build, **kw):
        kw.setdefault('lang', 'c++')
        super(Compiler, self).__init__(build, **kw)

    @property
    def _lang_flag(self):
        return self._flag('Tp')

    def _get_build_flags(self, cmd, **kw):
        return [
            self._flag('EHsc'), # catches C++ exceptions only and tells the
                                # compiler to assume that extern C functions
                                # never throw a C++ exception.
        ] + super(Compiler, self)._get_build_flags(cmd, **kw)
