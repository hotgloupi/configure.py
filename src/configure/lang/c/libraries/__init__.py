# -*- encoding: utf-8 -*-

from .sdl import SDLLibrary, SDLDependency, SDLImageDependency
from .python import PythonLibrary, PythonDependency
from .freetype import FreetypeLibrary, FreetypeDependency
from .opengl import OpenGLLibrary
from .curl import CURLDependency

from ..library import Library

def simple(name, compiler, **kw):
    return Library(name, compiler, **kw)
