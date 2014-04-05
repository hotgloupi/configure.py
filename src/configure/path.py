# -*- encoding: utf-8 -*-

import os.path
import stat

def exists(p, *paths):
    return os.path.exists(os.path.join(p, *paths))

def basename(p, *paths):
    return os.path.basename(os.path.join(p, *paths))

def splitext(p, *paths, **kw):
    return os.path.splitext(clean(p, *paths, **kw))

def clean(p, *paths, **kw):
    p = os.path.normpath(os.path.expanduser(os.path.join(p, *paths)))
    if p.startswith('./'):
        return p[2:]
    if kw.get('replace_home'):
        p = os.path.join(
            '~',
            os.path.relpath(p, start=os.path.expanduser('~')),
        )
    elif kw.get('absolute'):
        p = os.path.abspath(p)
    return p.replace('\\', '/')

join = clean

def dirname(p, *paths, **kw):
    return clean(os.path.dirname(os.path.join(p, *paths)), **kw)

def absolute(p, *paths, **kw):
    kw['absolute'] = True
    return clean(p, *paths, **kw)

def relative(p, *path, start=None, **kw):
    return clean(os.path.relpath(os.path.join(p, *path), start=start), **kw)

def is_absolute(p, *path):
    return os.path.isabs(os.path.join(p, *path))

is_directory = os.path.isdir

def is_executable(p, *path):
    path = os.path.join(p, *path)
    return (
        os.path.exists(path) and
        not os.path.isdir(path) and
        os.stat(path)[stat.ST_MODE] & stat.S_IXUSR
    )

def split(p, *path):
    dirname, basename = os.path.split(os.path.join(p, *path))
    return (clean(dirname), basename)

make_path = os.makedirs
