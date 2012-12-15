# -*- encoding: utf-8 -*-

from tupcfg.lang.c import gcc

class Compiler(gcc.Compiler):

    binary_name = 'g++'

    __standards_map = {
        'c++11': 'c++11',
    }

    def __init__(self, project, build, **kw):
        kw.setdefault('lang', 'cxx')
        super(Compiler, self).__init__(project, build, **kw)

    def _get_build_flags(self, cmd):
        return ['-x', 'c++'] + super(Compiler, self)._get_build_flags(cmd)
