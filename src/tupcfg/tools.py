# -*- encoding: utf-8 -*-

import os
import stat
import sys
import types

DEBUG = False
VERBOSE = True

def cleanpath(p, **kwargs):
    p = os.path.normpath(p).replace('\\', '/')
    if p.startswith('./'):
        return p[2:]
    if kwargs.get('replace_home'):
        return os.path.join(
            '~',
            os.path.relpath(p, start=os.path.expanduser('~')),
        )
    return p

def cleanabspath(p, **kwargs):
    return cleanpath(os.path.abspath(p), **kwargs)

def cleanjoin(*args, **kwargs):
    return cleanpath(os.path.join(*args), **kwargs)

def err(*args, **kwargs):
    kwargs['file'] = sys.stderr
    return print(*args, **kwargs)

warning = err
error = err
status = err

def debug(*args, **kwargs):
    if DEBUG:
        status(*args, **kwargs)

def verbose(*args, **kwargs):
    if VERBOSE:
        status(*args, **kwargs)

def fatal(*args, **kwargs):
    try:
        err(*args, **kwargs)
    finally:
        sys.exit(1)

def which(binary):
    paths = os.environ['PATH'].split(':')
    for dir_ in paths:
        path = os.path.join(dir_, binary)
        if os.path.exists(path) and os.stat(path)[stat.ST_MODE] & stat.S_IXUSR:
            return path
    return None

def find_binary(name):
    path = which(name)
    if path is None:
        raise Exception("Cannot find '%s'" % name)
    return path


def glob(pattern, dir_=None, recursive=False):
    from fnmatch import fnmatch
    if dir_ is None:
        dir_ = os.path.dirname(pattern)
        pattern = os.path.basename(pattern)

    for root, dirnames, files in os.walk(dir_):
        for file_ in files:
            if fnmatch(file_, pattern):
                yield cleanjoin(root, file_)
        if not recursive:
            break

def isiterable(obj):
    return isinstance(obj, (list, tuple, types.GeneratorType))
