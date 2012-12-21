# -*- encoding: utf-8 -*-

from ..library import Library

class FreetypeLibrary(Library):

    def __init__(self, compiler, **kw):
        super(FreetypeLibrary, self).__init__(
            'freetype',
            compiler,
            find_includes = [
                'ft2build.h',
                'freetype/config/ftconfig.h'
            ],
            include_directory_names = ['', 'freetype2'],
            shared=kw.get('shared', True)
        )
