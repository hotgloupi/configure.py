
from . import gcc
from configure.lang.c import clang as c_clang

from configure import platform, path

class Compiler(gcc.Compiler, c_clang.Compiler):
    name = 'clang'
    binary_name = 'clang++'

    def __init__(self, build, **kw):
        if platform.IS_MACOSX:
            kw.setdefault('stdlib', 'libc++')
        kw.setdefault('standard', 'c++11')
        super().__init__(build, **kw)
        if platform.IS_MACOSX and self.stdlib == 'libc++':
            prefix = path.join(path.dirname(self.binary), '..', absolute = True)
            self.libraries.extend([
                self.find_library(
                    'libc++',
                    name_suffixes = ['', '.1'],
                    include_directory_names = ['../lib/c++/v1'],
                    find_includes = ['__config'],
                    prefixes = [prefix]
                ),
                #self.find_library('libc++abi'),
            ])


