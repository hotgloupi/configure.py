# -*- encoding: utf-8 -*-

from tupcfg import Source
import tupcfg.compiler

class CXXSource(Source):
    pass

class Compiler(tupcfg.compiler.Compiler):
    binary_env_varname = 'CXX'

    Source = CXXSource

