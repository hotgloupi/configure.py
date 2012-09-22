# -*- encoding: utf-8 -*-

import os

from .. import tools

def project():
    return tools.cleanjoin(
        os.path.dirname(__file__),
        "project.py"
    )
