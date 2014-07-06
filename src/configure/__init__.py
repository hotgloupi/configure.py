# -*- encoding: utf8 -*-

import sys
try:
    if sys.version_info[0] != 3:
        raise Exception("Invalid python version")
except:
    raise Exception("Invalid python version (should be >= 3)")

from . import tools, path, platform, lang

from .build import Build
from .command import Command
from .dependency import Dependency
from .env import Env, VariableNotFound
from .generator import Generator
from .node import Node
from .project import Project
from .source import Source
from .target import Target

