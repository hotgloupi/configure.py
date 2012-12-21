# -*- encoding: utf-8 -*-

from ..library import Library

from tupcfg import platform

class OpenGLLibrary(Library):

    def __init__(self, compiler, **kw):
        if platform.IS_WINDOWS:
            name = 'opengl32'
            components = ['glu32']
        elif platform.IS_MACOSX:
            name = 'OpenGL'
            components = ['Cocoa', 'CoreFoundation']
        else:
            name = 'GL'
            components = ['GLU']
        super(OpenGLLibrary, self).__init__(
            name,
            compiler,
            shared = kw.get('shared', True),
            macosx_framework = platform.IS_MACOSX,
        )
        self.components = list(
            Library(
                component,
                compiler,
                shared = kw.get('shared', True),
                macosx_framework = platform.IS_MACOSX
            ) for component in components
        )

    @property
    def libraries(self):
        return [self] + self.components


