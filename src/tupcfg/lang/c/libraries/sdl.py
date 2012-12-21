# -*- encoding: utf-8 -*-

from ..library import Library
from tupcfg import platform

class SDLLibrary(Library):
    def __init__(self, compiler, components=[], **kw):
        super(SDLLibrary, self).__init__(
            'SDL',
            compiler,
            find_includes = ['SDL/SDL.h'],
            shared = kw.get('shared', True),
        )
        self.components = list(
            Library('SDL_' + c, compiler, shared = kw.get('shared', True))
            for c in components
        )
        if platform.IS_MACOSX:
            self.components.append(Library('SDLMain')) # Fixture from SDL is needed

    @property
    def libraries(self):
        return [self] + self.components
