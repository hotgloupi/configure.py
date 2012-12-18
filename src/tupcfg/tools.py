# -*- encoding: utf-8 -*-

import os
import sys
import types
from . import path
from . import platform

DEBUG = False
VERBOSE = True

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

PATH_SPLIT_CHAR = platform.IS_WINDOWS and ';' or ':'

PATH = os.environ['PATH'].split(PATH_SPLIT_CHAR)

def which(binary):
    for dir_ in PATH:
        exe = os.path.join(dir_, binary)
        if path.is_executable(exe):
            return exe
    if platform.IS_WINDOWS and not binary.lower().endswith('.exe'):
        return which(binary + '.exe')
    return None

def find_binary(name, env=None, var_name=None):
    if not (env and var_name) and (env or var_name):
        raise Exception("Wrong usage, please set both env and var_name")
    if env and var_name:
        binary = env.get(var_name)
        if binary is not None and not path.is_absolute(binary):
            binary = which(binary)
        if path is not None:
            return path.clean(binary)
    binary = which(name)
    if path is None:
        if env and var_name:
            raise Exception(
                "Cannot find binary '%s' (try to set %s variable)" % (name, var_name)
            )
        else:
            raise Exception("Cannot find binary '%s'" % name)
    return binary


def glob(pattern, dir_=None, recursive=False):
    from fnmatch import fnmatch
    if dir_ is None:
        dir_ = os.path.dirname(pattern)
        pattern = os.path.basename(pattern)

    for root, dirnames, files in os.walk(dir_):
        for file_ in files:
            if fnmatch(file_, pattern):
                yield path.join(root, file_)
        if not recursive:
            break

def isiterable(obj):
    return isinstance(obj, (list, tuple, types.GeneratorType))

def _match_file(file_, name, extensions, prefixes, suffixes, validator):
    from fnmatch import fnmatch
    filename, ext = os.path.splitext(file_)
    if extensions:
        if len(ext):
            assert ext[0] == '.'
            ext = ext[1:]
        if ext not in extensions:
            return False
    matching_prefixes = ['']
    if prefixes:
        matching_prefixes = list(p for p in prefixes if filename.startswith(p))
        if not matching_prefixes:
            return False

    matching_suffixes = ['']
    if suffixes:
        matching_suffixes = list(p for p in suffixes if filename.endswith(p))
        if not matching_suffixes:
            return False

    for p in matching_prefixes:
        for s in matching_suffixes:
            if len(p) + len(s) > len(filename):
                continue
            if fnmatch(filename[len(p):len(filename) - len(s)], name):
                return True
    return False




def find_files(working_directory='.',
               name=None,
               extensions=None,
               prefixes=None,
               suffixes=None,
               validator=None):

    results = []
    for root, dirnames, files in os.walk(working_directory):
        results.extend(
            file_ for file_ in files if _match_file(
                file_,
                name,
                extensions,
                prefixes,
                suffixes,
                validator
            )
        )
    return results

