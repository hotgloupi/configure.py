# -*- encoding: utf-8 -*-

import sys

from . import path
from .source import Source
from .target import Target

class BasicCompiler:
    """Base class for all compiler"""

    def __init__(self, binary, project, build, lang=None):
        self.project = project
        self.build = build
        self.lang = lang
        self.binary = binary

    def link_library(self, name, sources, directory='', shared=True, ext=None, **kw):
        name = path.join(directory, self.__get_library_name(name, shared, ext))
        sources_ = (Source(src) for src in sources)
        objects = (self._build_object(src, **kw) for src in sources_)
        return self.build.add_target(
            Target(name, self._link_library(list(objects), shared=shared, **kw))
        )

    def link_static_library(self, name, sources, **kw):
        kw['shared'] = False
        return self.link_library(name, sources, **kw)

    def link_dynamic_library(self, name, sources, **kw):
        kw['shared'] = True
        return self.link_library(name, sources, **kw)

    def link_executable(self, name, sources, directory='', **kw):
        name = path.join(directory, self.__get_executable_name(name))
        sources_ = (Source(src) for src in sources)
        objects = (self._build_object(src, **kw) for src in sources_)
        return self.build.add_target(
            Target(name, self._link_executable(list(objects), **kw))
        )

    def _build_object(self, source, **kw):
        """Create a `Target` to build a object from source.

        This method has to be overridden.
        """
        raise Exception("Not implemented")

    def _link_library(self, objects, **kw):
        """Create a `Command` to link a library from objects.

        This method has to be overridden.
        """
        raise Exception("Not implemented")

    def _link_executable(self, objects, **kw):
        """Create a `Command` to link an executable from objects.

        This method has to be overridden.
        """
        raise Exception("Not implemented")

    def __get_library_name(self, name, shared, ext):
        shared_exts = {
            'win32': 'dll',
            'darwin': 'dylib',
        }
        static_exts = {
            'win32': 'a',
        }
        if ext is None:
            if shared:
                ext = shared_exts.get(sys.platform, 'so')
            else:
                ext = static_exts.get(sys.platform, 'a')
        if ext:
            return name + '.' + ext
        return name

    def __get_executable_name(self, name):
        if sys.platform == 'win32':
            return name + '.exe'
        return name

    def library_extensions(self, shared):
        raise Exception("Not implemented")
