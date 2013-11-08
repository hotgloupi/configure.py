# -*- encoding: utf-8 -*-

from tupcfg import Source, Target, Node

import tupcfg.compiler

class CSource(Source):
    pass

class Compiler(tupcfg.compiler.Compiler):
    binary_env_varname = 'CC'

    Source = CSource

    def __init__(self, project, build, **kw):
        kw.setdefault('lang', 'c')
        super().__init__(project, build, **kw)

    def build_object(self, src, **kw):
        target = super().build_object(src, **kw)
        pchs = self.list_attr('precompiled_headers', kw = kw)
        target.dependencies.extend(pchs)
        return target

    def generate_precompiled_header(self, source, force_include = False, **kw):
        build = self.attr('build', kw)
        cpy = build.fs.copy(source)
        target = Target(build, source + '.gch')
        command = self._build_object_cmd(
            target,
            cpy,
            precompiled_header = True,
            action = 'Build precompiled header',
            **kw
        )
        return target

