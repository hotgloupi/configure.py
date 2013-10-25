# -*- encoding: utf-8 -*-

import sys

from . import path, tools, platform, generators
from .command import Command
from .source import Source
from .target import Target

class Compiler:
    """Base class for all compiler.

    The Basic compiler provides most common API to compile source files into
    libraries or executables.
    """

    # Standard binary name (Should be overriden)
    binary_name = None

    # Environment variable name that might contain the binary name (Should be overriden)
    binary_env_varname = None

    # Compiled object extension
    object_extension = 'o'

    # Available compilers for this language
    compilers = []

    # Library class for this compiler / language
    Library = None

    def __init__(self, project, build, **kw):
        assert 'lang' in kw
        attrs = [
            ('defines', []),
            ('position_independent_code', False),
            ('standard', None),
            ('target_architecture', platform.ARCHITECTURE),
            ('force_architecture', True),
            ('enable_warnings', True),
            ('use_build_type_flags', True),
            ('hidden_visibility', True),
            ('additional_link_flags', {}),
            ('recursive_linking', True),
            ('generate_source_dependencies_for_makefile',
             any(isinstance(g, generators.Makefile) for g in build.generators)),

            ('stdlib', True),
            ('static_libstd', False),
            ('libraries', []),
            ('include_directories', []),
            ('library_directories', []),
            ('precompiled_headers', []),
            ('force_includes', [])
        ]
        self._set_attributes_default(attrs, kw)

        assert self.binary_name is not None
        assert self.binary_env_varname is not None

        binary = project.env.get('FORCE_%s' % self.binary_env_varname)
        if not binary:
            binary = tools.find_binary(self.binary_name, project.env, self.binary_env_varname)
        project.env.build_set(self.binary_env_varname, binary)
        lang = kw['lang']
        kw.pop('lang')
        if kw:
            tools.warning("Unused arguments given to %s:" % self.__class__.__name__)
            for item in kw.items():
                tools.warning("\tunused argument %s: %s" % item)
        self.project = project
        self.build = build
        self.lang = lang
        self.binary = binary

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

    def build_object(self, src, additional_inputs = [], **kw):
        """Create a `Target` to build an object from source using @a
        BuildObject command. It also generate the associated dependencies of
        that source file if any (like makefile includes).

        Returns the object target.
        """
        target = Target(
            src.filename + '.' + self.object_extension,
            self.BuildObject(self, src, **kw),
            additional_inputs = additional_inputs,
        )
        if self.generate_source_dependencies_for_makefile:
            mktarget = Target(
                src.filename + '.' + self.object_extension + '.depends.mk',
                self.BuildObjectDependencies(
                    self,
                    src,
                    target,
                    **kw
                )
            )
            mktarget.additional_inputs.extend(target.additional_inputs)
            target.additional_inputs.append(mktarget)
            kw.get('build', self.build).add_target(mktarget)
            #print('add', mktarget, 'to', kw.get('build', self.build.directory))
        return target #kw.get('build', self.build).add_target(target)

    def link_executable(self, name, sources, directory='', ext=None, **kw):
        """Build a list of sources into a library.

        Calls build_objects for intermediate objects, and use LinkExecutable
        for final linking.
        """
        name = path.join(str(directory), self.__get_executable_name(name, ext))
        sources_ = (Source(src) for src in sources)
        objects = (self.build_object(src, **kw) for src in sources_)
        return kw.get('build', self.build).add_target(
            Target(name, self.LinkExecutable(self, list(objects), **kw))
        )

    def link_library(self,
                     name,
                     sources,
                     directory = '',
                     shared = True,
                     ext = None,
                     additional_inputs = [],
                     **kw):
        """Build a list of sources into a library.

        Calls build_objects for intermediate objects, and use LinkLibrary for
        final linking.
        """
        name = path.join(str(directory), self.__get_library_name(name, shared, ext))
        sources_ = (Source(src) for src in sources)
        objects = (
            self.build_object(src, additional_inputs = additional_inputs, **kw)
            for src in sources_
        )
        return kw.get('build', self.build).add_target(
            Target(
                name,
                self.LinkLibrary(
                    self,
                    list(objects),
                    shared = shared,
                    **kw
                ),
                additional_inputs = additional_inputs,
            )
        )

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

    def _set_attributes_default(self, attrs, kw):
        for key, default in attrs:
            setattr(self, key, kw.get(key, default))
            if key in kw:
                kw.pop(key)

    def attr(self, attribute, cmd):
        """Returns an attribute value with correct priority"""
        return cmd.kw.get(attribute, getattr(self, attribute))



    class BuildObject(Command):
        """Calls _build_object_cmd compiler method."""

        @property
        def action(self):
            return "Building %s object" % self.compiler.lang

        def __init__(self, compiler, source, **kw):
            if not isinstance(source, (Source, Target)):
                raise Exception(
                    "Cannot build compiler object from '%s' (of type %s): should be a Source or a Target instance" %
                    (source, type(source))
                )
            self.compiler = compiler
            self.source = source
            self.kw = kw
            Command.__init__(self, source)

        def command(self, **kw):
            cmd = self.compiler._build_object_cmd(self, **kw)
            return cmd

    class BuildObjectDependencies(Command):
        """Calls _build_object_dependencies_cmd compiler method."""

        @property
        def action(self):
            return "Building %s object dependencies" % self.compiler.lang

        def __init__(self, compiler, source, target, **kw):
            self.compiler = compiler
            self.source = source
            self.target = target
            self.kw = kw
            assert isinstance(source, Source)
            assert isinstance(target, Target)
            Command.__init__(self, source)

        def command(self, **kw):
            return self.compiler._build_object_dependencies_cmd(self, **kw)

    class LinkCommand(Command):
        """Base class for linking commands"""

        def __init__(self, compiler, objects, **kw):
            self.compiler = compiler
            self.objects = objects
            self.kw = kw
            Command.__init__(self, objects)

    class LinkExecutable(LinkCommand):
        """Calls _link_executable_cmd compiler method."""
        action = "Linking executable"
        def command(self, **kw):
            return self.compiler._link_executable_cmd(self, **kw)

    class LinkLibrary(LinkCommand):
        """Calls _link_library_cmd compiler method."""
        action = "Linking library"

        def __init__(self, compiler, objects, shared=True, **kw):
            self.shared = shared
            super().__init__(compiler, objects, **kw)

        def command(self, **kw):
            return self.compiler._link_library_cmd(self, **kw)

    def _include_directories(self, cmd):
        include_directories = self.include_directories[:]
        include_directories += self.include_directories + \
                cmd.kw.get('include_directories', [])
        libraries = self.libraries + cmd.kw.get('libraries', [])
        for lib in libraries:
            if isinstance(lib, Target):
                continue
            include_directories.extend(lib.include_directories)

        class RelativeDirectory:
            def __init__(self, dir_):
                self._dir = dir_
            def shell_string(self, cwd=None, build=None):
                return path.relative(self._dir, start = cwd)

        dirs = []
        for dir_ in tools.unique(include_directories):
            if isinstance(dir_, str) and \
               path.absolute(dir_).startswith(self.project.directory):
                dirs.append(RelativeDirectory(dir_))
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
