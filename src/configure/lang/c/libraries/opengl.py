# -*- encoding: utf-8 -*-

from ..library import Library

from configure import platform

class OpenGLLibrary(Library):

    def __init__(self, compiler, **kw):
        components = []
        binary_file_names = ['GL']#, 'GLU']
        if platform.IS_WINDOWS:
            name = 'opengl32'
            binary_file_names = ['opengl32']#, 'glu32']
        elif platform.IS_MACOSX:
            name = 'OpenGL'
            components = ['Cocoa', 'CoreFoundation']
        else:
            name = 'GL'

        kw.setdefault('macosx_framework', platform.IS_MACOSX)
        super().__init__(
            name,
            compiler,
            shared = kw.pop('shared', True),
            binary_file_names = binary_file_names,
            **kw
        )

        self.components = list(
            Library(
                component,
                compiler,
                shared = kw.get('shared', True),
                macosx_framework = platform.IS_MACOSX
            ) for component in components
        )

        self.libraries = [self] + self.components


