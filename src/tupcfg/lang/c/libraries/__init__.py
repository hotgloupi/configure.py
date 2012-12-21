# -*- encoding: utf-8 -*-

from .sdl import SDLLibrary
from .python import PythonLibrary
from .freetype import FreetypeLibrary
from .opengl import OpenGLLibrary

from ..library import Library

def simple(name, compiler, **kw):
    return Library(name, compiler, **kw)
