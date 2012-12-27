# -*- encoding: utf-8 -*-

from tupcfg import compiler, tools, path, Target, Command, Source, platform

class Compiler(compiler.BasicCompiler):
    """Generic compiler."""

    # Standard binary name (Should be overriden)
    binary_name = None

    # Compiled object extension
    object_extension = 'o'

    def library_extensions(self, shared, for_linker=False):
        if shared:
            if platform.IS_MACOSX:
                return ['dylib']
            else:
                return ['so']
        else:
            return ['a']

    class BuildObject(Command):
        """Basic behavior to build an object from source"""

        @property
        def action(self):
            return "Building %s object" % self.compiler.lang

        def __init__(self, compiler, source, **kw):
            if not isinstance(source, Source):
                raise Exception(
                    "Cannot build object from '%s' (of type %s)" %
                    (source, type(source))
                )
            self.compiler = compiler
            self.kw = kw
            Command.__init__(self, source)

        def command(self, **kw):
            return self.compiler._build_object_cmd(self, **kw)

    class LinkCommand(Command):
        """Base class for linking commands"""

        def __init__(self, compiler, objects, **kw):
            self.compiler = compiler
            self.kw = kw
            Command.__init__(self, objects)

    class LinkExecutable(LinkCommand):
        action = "Linking executable"
        def command(self, **kw):
            return self.compiler._link_executable_cmd(self, **kw)

    class LinkLibrary(LinkCommand):
        action = "Linking library"

        def __init__(self, compiler, objects, shared=True, **kw):
            self.shared = shared
            Compiler.LinkCommand.__init__(self, compiler, objects, **kw)

        def command(self, **kw):
            return self.compiler._link_library_cmd(self, **kw)

    def _include_directories(self, cmd):
        include_directories = (
            self.include_directories +
            cmd.kw.get('include_directories', [])
        )
        libraries = cmd.kw.get('libraries', [])
        for lib in libraries:
            if isinstance(lib, Target):
                continue
            include_directories.extend(lib.include_directories)

        class RelativeDirectory:
            def __init__(self, dir_):
                self._dir = dir_
            def shell_string(self, target=None, build=None):
                return path.relative(self._dir, start = target.directory(build))

        dirs = []
        for dir_ in tools.unique(include_directories):
            if path.absolute(dir_).startswith(self.project.directory):
                dirs.append(RelativeDirectory(dir_))
            else:
                dirs.append(dir_)

        return dirs

    def __init__(self, project, build, **kw):
        assert 'lang' in kw
        attrs = [
            ('defines', []),
            ('library_directories', []),
            ('include_directories', []),
            ('position_independent_code', False),
            ('standard', None),
            ('architecture', platform.ARCHITECTURE),
            ('enable_warnings', True),
            ('use_build_type_flags', True),
            ('hidden_visibility', True),
            ('static_libstd', False),
        ]
        for key, default in attrs:
            setattr(self, key, kw.get(key, default))
            if key in kw:
                kw.pop(key)
        assert self.binary_name is not None
        binary = project.env.get('FORCE_CXX')
        if not binary:
            binary = tools.find_binary(self.binary_name, project.env, 'CXX')
        project.env.project_set('CXX', binary)
        super(Compiler, self).__init__(binary, project, build, **kw)

    def attr(self, attribute, cmd):
        """Returns an attribute value with correct priority"""
        return cmd.kw.get(attribute, getattr(self, attribute))

    def _build_object(self, src, **kw):
        return Target(
            src.filename + '.' + self.object_extension,
            self.BuildObject(self, src, **kw)
        )

    def _link_library(self, objects, **kw):
        return self.LinkLibrary(self, objects, **kw)

    def _link_executable(self, objects, **kw):
        return self.LinkExecutable(self, objects, **kw)
