
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
        if platform.IS_OSX and self.stdlib == 'libc++':
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

    def _get_build_flags(self, kw):
        flags = super()._get_build_flags(kw)
        if platform.IS_OSX and platform.OSX_VERSION_MAJOR < 10 and or \
          (platform.OSX_VERSION_MAJOR == 10 and platform.OSX_VERSION_MINOR <= 6):
            # Bug in math.h on OS X 10.6
            flags.append('-U__STRICT_ANSI__')
        return flags

