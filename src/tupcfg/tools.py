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

def find_binary(name, env=None, var_name=None):
    if not (env and var_name) and (env or var_name):
        raise Exception("Wrong usage, please set both env and var_name")
    if env and var_name:
        path = env.get(var_name)
        if path is not None and not os.path.isabs(path):
            path = which(path)
        if path is not None:
            return path
    path = which(name)
    if path is None:
        if env and var_name:
            raise Exception(
                "Cannot find binary '%s' (try to set %s variable)" % (name, var_name)
            )
        else:
            raise Exception("Cannot find binary '%s'" % name)
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
