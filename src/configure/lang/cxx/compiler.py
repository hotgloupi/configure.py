# -*- encoding: utf-8 -*-

from configure import Source
import configure.compiler

class CXXSource(Source):
    pass

class Compiler(configure.compiler.Compiler):
    binary_env_varname = 'CXX'

    Source = CXXSource

