# -*- encoding: utf-8 -*-

import sys

from . import path, tools, platform, generators
from .command import Command
from .source import Source
from .target import Target
from .node import Node

class Compiler:
    """Base class for all compiler.

    The Basic compiler provides most common API to compile source files into
    libraries or executables.
    """

    # Standard compiler name (defined by subclasses).
    name = None

    # Standard binary name (defined by subclasses).
    binary_name = None

    # Environment variable name that might contain the binary name.
    binary_env_varname = None

    # Compiled object extension
    object_extension = 'o'

    # Available compilers for this language
    compilers = []

    # Library class for this compiler / language
    Library = None

    supported_warnings = [
        'unused_typedefs',
    ]

    # Compiler attributes and their default value. All of those attributes can
    # be used in the compiler constructor, through all build commands or
    # accessed later as normal instance attributes. Note that subclasses might
    # add attributes to that list.
    attributes = [
        ('lang', None),
        ('defines', []),
        ('position_independent_code', False),
        ('standard', None),
        ('target_architecture', platform.ARCHITECTURE),
        ('force_architecture', True),
        ('enable_warnings', True),
        ('use_build_type_flags', True),
        ('hidden_visibility', True),
        ('additional_link_flags', {}),
        ('recursive_linking', not platform.IS_MACOSX),
        ('generate_source_dependencies_for_makefile', False),
        ('stdlib', True),
        ('static_libstd', False),
        ('libraries', []),
        ('include_directories', []),
        ('library_directories', []),
        ('precompiled_headers', []),
        ('force_includes', []),
        ('disabled_warnings', ['unused_typedefs',]),
    ]

    def __init__(self, project, build, **kw):
        assert self.name is not None
        assert self.binary_name is not None
        assert self.binary_env_varname is not None
        self.project = project
        self.build = build

        binary = project.env.get('FORCE_%s' % self.binary_env_varname)
        if not binary:
            binary = tools.find_binary(self.binary_name, project.env, self.binary_env_varname)
        project.env.build_set(self.binary_env_varname, binary)
        self.binary = binary

        self.__set_attributes(self.attributes, kw)

        if kw:
            tools.warning("Unused arguments given to %s:" % self.__class__.__name__)
            for item in kw.items():
                tools.warning("\tUnused argument %s: %s" % item)

        for warning in self.disabled_warnings:
            if warning not in self.supported_warnings:
                tools.warning("Unknown warning name:", warning)


    @classmethod
    def from_bin(cls, bin, *args, **kw):
        for c in cls.compilers:
            if c.binary_name in bin.lower():
                return c(*args, **kw)
        raise Exception(
            "Cannot detect %s compiler from binary %s" % (cls.lang, bin)
        )

    @classmethod
    def find_compiler(cls, project, build, **kw):
        cc = project.env.get(cls.binary_env_varname)
        if cc is not None:
            bin = tools.find_binary(cc)
            return cls.from_bin(bin, project, build, **kw)

        search_binary_files = [c.binary_name for c in cls.compilers]
        for i, bin in enumerate(search_binary_files):
            if tools.which(bin):
                return cls.compilers[i](project, build, **kw)
        raise Exception("Cannot detect any %s compiler" % cls.lang)


    def find_library(self, name, **kw):
        return self.Library(name, self, **kw)

    def __str__(self):
        return '%s compiler \'%s\' (%s)' % (self.lang, self.name, self.binary)

    def build_object(self, src, **kw):
        """Create a `Target` to build an object from source using @a
        BuildObject command. It also generate the associated dependencies of
        that source file if any (like makefile includes).

        Returns the object target.
        """
        build = self.attr('build', kw)
        assert isinstance(src, Node)
        target = Target(build, src.relative_path + '.' + self.object_extension)
        command = self._build_object_cmd(target, src, **kw)

        if self.attr('generate_source_dependencies_for_makefile', kw):
            mktarget = Target(
                build,
                src.relative_path + '.' + self.object_extension + '.depends.mk',
            )
            mkcmd = self._build_object_dependencies_cmd(
                mktarget,
                target,
                src,
                **kw
            )
            assert isinstance(mkcmd, Command)
            target.dependencies.append(mktarget)
        return target

    def _build_object_cmd(self, target, sources, **kw):
        """Implementation specific code that returns a command instance."""
        return NotImplemented

    def _build_object_dependencies_cmd(self, target, object, source, **kw):
        """Implementation specific code that returns a command instance."""
        return NotImplemented

    def link_executable(self, name, sources, directory='', ext=None, **kw):
        """Build a list of sources into a library.

        Calls build_objects for intermediate objects, and returns the targetted
        executable.
        """
        build = self.attr('build', kw)
        name = path.join(str(directory), self.__get_executable_name(name, ext))
        target = Target(build, name)
        objects = list(
            self.build_object(Source(build, src), **kw) for src in sources
        )
        command = self._link_executable_cmd(target, objects, **kw)
        assert isinstance(command, Command)
        assert command.target is target
        return target

    def _link_executable_cmd(self, target, objects, **kw):
        """Implementation specific code that returns a command instance."""
        return NotImplemented

    def link_library(self,
                     name,
                     sources,
                     directory = '',
                     shared = True,
                     ext = None,
                     **kw):
        """Build a list of sources into a library.

        Calls build_objects for intermediate objects, and returns the targetted
        library.
        """
        build = self.attr('build', kw)
        name = path.join(str(directory), self.__get_library_name(name, shared, ext))
        sources_ = (Source(build, src) for src in sources)
        objects = list(self.build_object(src, **kw) for src in sources_)
        target = Target(build, name)
        command = self._link_library_cmd(target, objects, shared = shared, **kw)
        assert isinstance(command, Command)
        assert command.target is target
        return target


    def _link_library_cmd(self, target, objects, shared = None, **kw):
        """Implementation specific code that returns a command instance."""
        return NotImplemented

    def link_static_library(self, name, sources, **kw):
        """Forward to link_library."""
        kw['shared'] = False
        return self.link_library(name, sources, **kw)

    def link_dynamic_library(self, name, sources, **kw):
        """Forward to link_library."""
        kw['shared'] = True
        return self.link_library(name, sources, **kw)


    def executable_extension(self):
        if sys.platform == 'win32':
            return 'exe'
        return ''

    def library_extension(self, shared):
        """Generic library extensions.
        """
        return self.library_extensions(shared)[0]

    def library_extensions(self, shared, for_linker = False):
        if shared:
            if platform.IS_MACOSX:
                return ['dylib', 'so']
            elif platform.IS_WINDOWS:
                return ['dll', 'so']
            else:
                return ['so']
        else:
            if platform.IS_WINDOWS:
                return ['a', 'lib']
            else:
                return ['a']

    def __set_attributes(self, attrs, kw):
        for key, default in attrs:
            setattr(self, key, kw.get(key, default))
            if key in kw:
                kw.pop(key)

    def attr(self, attribute, kw):
        """Returns an attribute value with correct priority"""
        assert isinstance(kw, dict)
        return kw.get(attribute, getattr(self, attribute))

    def list_attr(self, attribute, kw):
        """Returns the sum of the compiler and the command attributes."""
        assert isinstance(kw, dict)
        return kw.get(attribute, []) + getattr(self, attribute)

    def _include_directories(self, kw):
        include_directories = self.list_attr('include_directories', kw)
        libraries = self.list_attr('libraries', kw)
        for lib in libraries:
            if isinstance(lib, Target):
                continue
            include_directories.extend(lib.include_directories)

        dirs = []
        for dir_ in tools.unique(include_directories):
            if isinstance(dir_, str) and \
               path.absolute(dir_).startswith(self.project.directory):
                dirs.append(Source(self.attr('build', kw), dir_))
            else:
                dirs.append(dir_)
        return dirs

    def __get_library_name(self, name, shared, ext):
        if ext is None:
            ext = self.library_extension(shared)
        if ext:
            return name + '.' + ext
        return name

    def __get_executable_name(self, name, ext):
        if ext is None:
            ext = self.executable_extension()
        if ext:
            return name + '.' + ext
        return name
