# -*- encoding: utf-8 -*-

from . import gcc

class Compiler(gcc.Compiler):
    name = 'clang'
    binary_name = 'clang'
