# -*- encoding: utf-8 -*-

from ..library import Library

from sysconfig import get_config_var as var

class PythonLibrary(Library):
    def __init__(self, compiler, **kw):
        include_dir = var('INCLUDEPY')
        assert include_dir is not None
        prefix = var('prefix')
        assert prefix is not None
        super(PythonLibrary, self).__init__(
            "python" + var('LDVERSION'),
            compiler,
            find_includes = ['Python.h'],
            prefixes = [prefix],
            include_directories = var('INCLUDEPY') and [var('INCLUDEPY')] or [],
            directories = var('LIBPL') and [var('LIBPL')] or [],
            shared = kw.get('shared', True),
        )
        self.ext = var('SO')[1:]
        #version = var('py_version_nodot')
        #lib_dirs = []
        #for d in ['lib', 'Libs', 'DLLs']:
        #    if path.exists(prefix, d, 'libpython' + version + '.a') or \
        #       path.exists(prefix, d, 'python' + version + '.lib') or \
        #       path.exists(prefix, d, 'python' + version[0] + '.dll') or \
        #       path.exists(prefix, d, 'libpython' + version + '.so') or \
        #       path.exists(prefix, d, 'libpython' + version + '.dylib'):
        #        lib_dirs.append(path.join(prefix, d))
        #if platform.IS_MACOSX:
        #    lib_dir = var('LIBPL')
        #    assert path.exists(lib_dir)
        #    name = 'python' + var('py_version_short')
        #    assert path.exists(lib_dir, 'lib' + name + '.dylib')
        #    lib_dirs.append(lib_dir)
        #else:
        #    name = 'python' + (var('LDVERSION') or version)
        #print('PYTHON lib dirs:', ', '.join(lib_dirs))
        #Library.__init__(self, name, [include_dir], lib_dirs, **kw)
