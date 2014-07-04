# -*- encoding: utf-8 -*-

NAME = "configure.py"
VERSION_NAME = "alpha"

from configure.tools import rglob

def main(project, build):
    print("Configuring project", project.env.NAME, 'in', build.directory)
    for src in rglob('*.py', dir = 'src/'):
        build.fs.copy(src, src[4:])
