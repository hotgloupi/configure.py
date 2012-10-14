# -*- encoding: utf-8 -*-

from .. import path

def project():
    return path.join(
        path.dirname(__file__),
        "project.py"
    )
