# -*- encoding: utf-8 -*-

from tupcfg import compiler, tools, Target, Command, Source


class Compiler(compiler.BasicCompiler):
    """Generic CXX compiler."""

    # Standard binary name (Should be overriden)
    binary_name = None

    class BuildObject(Command):
        """Basic behavior to build an object from source"""
        action = "Building CXX object"

        def __init__(self, compiler, source, libraries=[]):
            if not isinstance(source, Source):
                raise Exception(
                    "Cannot build object from '%s' (of type %s)" %
                    (source, type(source))
                )
            self.compiler = compiler
            self.libraries = libraries
            Command.__init__(self, source)

        def command(self, **kw):
            return self.compiler._build_object_cmd(self, **kw)

    class LinkCommand(Command):
        """Base class for linking commands"""

        def __init__(self, compiler, objects, libraries=[]):
            self.compiler = compiler
            self.libraries = libraries
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

    def __init__(self, project, build, **kw):
        kw['lang'] = 'cxx'
        attrs = [
            ('library_directories', []),
            ('include_directories', []),
            ('position_independent_code', False),
            ('standard', None),
        ]
        for key, default in attrs:
            setattr(self, key, kw.get(key, default))
            if key in kw:
                kw.pop(key)
        assert self.binary_name is not None
        binary = tools.find_binary(self.binary_name, project.env, 'CXX')
        project.env.project_set('CXX', binary)
        super(Compiler, self).__init__(binary, project, build, **kw)

    def _build_object(self, src, **kw):
        return (
            Target(src.filename + '.o', self.BuildObject(self, src, **kw))
        )

    def _link_library(self, objects, **kw):
        return self.LinkLibrary(self, objects, **kw)

    def _link_executable(self, objects, **kw):
        return self.LinkExecutable(self, objects, **kw)
