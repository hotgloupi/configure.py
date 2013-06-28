# -*- encoding: utf-8 -*-

NAME = "tupcfg"
VERSION_NAME = "alpha"

from tupcfg.tools import rglob

def configure(project, build):
    print("Configuring project", project.env.NAME, 'in', build.directory)
    for src in rglob('*.py', dir = 'src/'):
        build.fs.copy(src, src[4:])
