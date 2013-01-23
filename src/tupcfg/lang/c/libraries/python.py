# -*- encoding: utf-8 -*-

from ..library import Library
from tupcfg import path

from sysconfig import get_config_var as var

class PythonLibrary(Library):
    def __init__(self, compiler,
                 preferred_shared=True,
                 executable=None,
                 **kw):
        include_dir = var('INCLUDEPY')
        assert include_dir is not None
        prefix = var('prefix')
        assert prefix is not None

        directories = []
        if var('LIBPL'):
            directories.append(var('LIBPL'))
        if var('base'):
            directories.append(path.join(var('base'), 'libs'))
            directories.append(path.join(var('base'), 'DLLs'))
        name_suffixes = ['', var('py_version')[0]]
        for k in ['LDVERSION', 'py_version_nodot', 'py_version_short']:
            if var(k):
                name_suffixes.append(var(k))

        super(PythonLibrary, self).__init__(
            "python",
            compiler,
            find_includes = ['Python.h'],
            name_suffixes = name_suffixes,
            prefixes = [prefix],
            include_directories = var('INCLUDEPY') and [var('INCLUDEPY')] or [],
            directories = directories,
            preferred_shared = preferred_shared,
        )
        components = []
        if False and not shared:
            components = ['pyexpat', 'unicodedata']
        self.components = list(
            Library(
                component,
                compiler,
                prefixes = [prefix],
                include_directories = var('INCLUDEPY') and [var('INCLUDEPY')] or [],
                directories = directories,
                shared = shared,
            ) for component in components
        )

        self.ext = var('SO')[1:]

    @property
    def libraries(self):
        return [self] + self.components
