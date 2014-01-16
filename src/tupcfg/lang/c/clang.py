# -*- encoding: utf-8 -*-

from . import gcc

class Compiler(gcc.Compiler):
    name = 'clang'
    binary_name = 'clang'

    __warnings_map = {}
    __warnings_map.update(gcc.Compiler.__warnings_map)
    __warnings_map.pop('unused-typedefs')

