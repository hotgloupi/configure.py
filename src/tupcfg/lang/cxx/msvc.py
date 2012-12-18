
from tupcfg.lang.c import msvc

class Compiler(msvc.Compiler):

    def __init__(self, project, build, **kw):
        kw.setdefault('lang', 'cxx')
        super(Compiler, self).__init__(project, build, **kw)

    @property
    def _lang_flag(self):
        return self._flag('Tp')

    def _get_build_flags(self, cmd, **kw):
        return [
            self._flag('EHsc'), # catches C++ exceptions only and tells the
                                # compiler to assume that extern C functions
                                # never throw a C++ exception.
        ] + super(Compiler, self)._get_build_flags(cmd, **kw)
