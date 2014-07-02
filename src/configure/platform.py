# -*- encoding: utf-8 -*-

import sys

IS_WINDOWS = sys.platform.lower().startswith('win')
IS_MACOSX = sys.platform.lower().startswith('darwin')
IS_LINUX = sys.platform.lower().startswith('linux')

# make sure the platform is recognized
assert(IS_WINDOWS or IS_MACOSX or IS_LINUX)

# make sure only one of them is true
assert(int(IS_WINDOWS) + int(IS_MACOSX) + int(IS_LINUX) == 1)

import platform as _platform

ARCHITECTURE = _platform.architecture()[0]
BINARY_FORMAT = _platform.architecture()[1]
if IS_MACOSX and not BINARY_FORMAT:
    BINARY_FORMAT = 'macho'
try:
    BINARY_FORMAT = {
        'ELF': 'elf',
        'macho': 'macho',
        'WindowsPE': 'pe',
    }[BINARY_FORMAT]
except KeyError:
    raise Exception("'%s' binary format not handled, add it to this file (%s)" % (BINARY_FORMAT, __file__))
try:
    PROCESSOR = _platform.uname().machine
except AttributeError:
    # python3.2 has not yet named tuple.
    PROCESSOR = _platform.uname()[4]

#print("PROCESSOR:", PROCESSOR)
#print("BINARY_FORMAT:", BINARY_FORMAT)
#print("ARCHITECTURE:", ARCHITECTURE)
#print("platform.ARCHITECTURE:", _platform.architecture())
#print("UNAME:", _platform.uname())
