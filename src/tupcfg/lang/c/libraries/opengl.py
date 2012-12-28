# -*- encoding: utf-8 -*-

from ..library import Library

from tupcfg import platform

class OpenGLLibrary(Library):

    def __init__(self, compiler, **kw):
        components = []
        if platform.IS_WINDOWS:
            name = 'opengl32'
            binary_file_names = ['opengl32', 'glu32']
        elif platform.IS_MACOSX:
            name = 'OpenGL'
            components = ['Cocoa', 'CoreFoundation']
            binary_file_names = ['GL', 'GLU']
        else:
            name = 'GL'
            binary_file_names = ['GL', 'GLU']

        super(OpenGLLibrary, self).__init__(
            name,
            compiler,
            shared = kw.get('shared', True),
            macosx_framework = platform.IS_MACOSX,
            binary_file_names = binary_file_names,
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


