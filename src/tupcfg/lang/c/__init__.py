# -*- encoding: utf-8 -*-

from .compiler import Compiler
from . import gcc
from . import msvc
from . import clang
from . import libraries
from .library import Library

Compiler.compilers = [
    msvc.Compiler,
    clang.Compiler,
    gcc.Compiler,
]

def compiler_from_bin(bin, *args, **kw):
    return Compiler.compiler_from_bin(bin, *args, **kw)

def find_compiler(project, build, **kw):
    return Compiler.find_compiler(project, build, **kw)
