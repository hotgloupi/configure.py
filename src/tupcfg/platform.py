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
PROCESSOR = _platform.uname().machine
