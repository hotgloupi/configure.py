# -*- encoding: utf-8 -*-

from .source import Source
from .target import Target

class BasicCompiler:
    """Base class for all compiler"""

    def __init__(self, binary, project, build, lang=None):
        self.project = project
        self.build = build
        self.lang = lang
        self.binary = binary

    def link_library(self, name, sources, **kw):
        sources_ = (Source(src) for src in sources)
        objects = (self._build_object(src, **kw) for src in sources_)
        return self.build.add_target(
            Target(name, self._link_library(list(objects), **kw))
        )

    def link_static_library(self, name, sources, **kw):
        kw['shared'] = False
        return self.link_library(name, sources, **kw)

    def link_dynamic_library(self, name, sources, **kw):
        kw['shared'] = True
        return self.link_library(name, sources, **kw)

    def link_executable(self, name, sources, **kw):
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
