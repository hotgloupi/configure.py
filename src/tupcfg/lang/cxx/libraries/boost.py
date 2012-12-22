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

        self.components = []
        for component in components:
            shared = kw.get('%s_shared' % component, kw.get('shared', True))
            if shared:
                name_prefixes = ['']
            else:
                name_prefixes = ['lib']
            self.components.append(
                Library(
                    "boost_" + component,
                    compiler,
                    prefixes = self.prefixes,
                    include_directories = self.include_directories,
                    directories = self.directories,
                    shared = shared,
                    name_prefixes = name_prefixes,
                )
            )

    @property
    def libraries(self):
        return self.components

