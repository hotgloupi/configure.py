
from . import gcc
from tupcfg.lang.c import clang as c_clang

from tupcfg import platform, path

class Compiler(gcc.Compiler, c_clang.Compiler):
    name = 'clang'
    binary_name = 'clang++'

    def __init__(self, project, build, **kw):
        kw.setdefault(
            'stdlib',
            platform.IS_MACOSX and 'libc++' or True,
        )
        super().__init__(project, build, **kw)
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


