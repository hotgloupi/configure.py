# -*- encoding: utf-8 -*-

from ..library import Library

class BoostLibrary(Library):
    def __init__(self, compiler, components=[], **kw):
        super(BoostLibrary, self).__init__(
            "boost",
            compiler,
            find_includes=['boost/config.hpp'],
            search_binary_files = False,
        )
        self.components = list(
            Library(
                "boost_" + component,
                compiler,
                prefixes = self.prefixes,
                include_directories = self.include_directories,
                directories = self.directories,
                shared = kw.get('%s_shared', kw.get('shared', True)),
            )
            for component in components
        )

    @property
    def libraries(self):
        return self.components

