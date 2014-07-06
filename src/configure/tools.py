# -*- encoding: utf-8 -*-
from __future__ import print_function

import os
import sys
import types
from . import path
from . import platform

DEBUG = False
VERBOSE = True

def err(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)

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
        if binary is not None:
            return path.clean(binary)
    binary = which(name)
    if binary is None:
        if env and var_name:
            raise Exception(
                "Cannot find binary '%s' (try to set %s variable)" % (name, var_name)
            )
        else:
            raise Exception("Cannot find binary '%s'" % name)
    return path.clean(binary)


def glob(pattern, dir=None, recursive=False):
    from fnmatch import fnmatch
    if dir is None:
        dir = os.path.dirname(pattern)
        pattern = os.path.basename(pattern)

    for root, dirnames, files in os.walk(dir):
        for file_ in files:
            p = path.relative(root, file_, start=dir)
            if fnmatch(p, pattern):
                yield path.join(root, file_)
        if not recursive:
            break

def rglob(pattern, dir=None):
    return glob(pattern, dir=dir, recursive = True)

def isiterable(obj):
    return not isinstance(obj, str) and hasattr(obj, '__iter__')

def _match_file(root, file_, name, extensions, prefixes, suffixes, validator):
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
                if validator is not None:
                    return validator(path.join(root, file_))
                else:
                    return True
    return False

_walked = {}
def _walk(dir_):
    p  = path.absolute(dir_)
    res = _walked.get(p)

    if res is None:
        for root, dirs, files in os.walk(dir_):
            _walked[p] = root, dirs, files
            yield root, dirs, files
    else:
        root, dirs, files = res
        yield res
        for dir_ in dirs:
            yield _walk(path.join(root, dir_))


def find_files(working_directory='.',
               name=None,
               extensions=None,
               prefixes=None,
               suffixes=None,
               validator=None,
               recursive=True):

    if extensions:
        extensions = list(
            ext.startswith('.') and ext[1:] or ext
            for ext in extensions
        )
    results = []
    for root, dirnames, files in _walk(working_directory):
        results.extend(
            os.path.join(root, file_) for file_ in files if _match_file(
                root,
                file_,
                name,
                extensions,
                prefixes,
                suffixes,
                validator
            )
        )
        if not recursive:
            break
    return results


def unique(seq):
    seen = {}
    result = []
    for item in seq:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result

def python_command(file = None, module = None, args = []):
    path = os.environ.get('PYTHONPATH', '')
    if module is not None:
        return ['PYTHONPATH=%s' % path, sys.executable, '-m', module] + args
    elif file is not None:
        return ['PYTHONPATH=%s' % path, sys.executable, file] + args
    else:
        raise Exception("You must specify file or module argument")


from unittest import TestCase

class _(TestCase):

    def test_unique(self):
        seq = ['a', 1, 'b', 'a', 2, 1, 'c']
        self.assertEqual(
            unique(seq),
            ['a', 1, 'b', 2, 'c']
        )

    def test_isiterable(self):
        self.assertTrue(isiterable(set()))
        self.assertTrue(isiterable(list()))
        self.assertTrue(isiterable(tuple()))
        self.assertTrue(isiterable(range(10)))
        self.assertTrue(isiterable(i for i in range(10)))
        def gen():
            while True:
                yield "something"
        self.assertTrue(isiterable(gen()))

