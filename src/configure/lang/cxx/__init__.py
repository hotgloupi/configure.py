# -*- encoding: utf-8 -*-

from .compiler import Compiler
from . import gcc
from . import clang
from . import msvc
from . import libraries
from .library import Library

Compiler.compilers = [
    msvc.Compiler,
    clang.Compiler,
    gcc.Compiler,
]

def find_compiler(build, name = None, **kw):
    return Compiler.find_compiler(build, name = name, **kw)
