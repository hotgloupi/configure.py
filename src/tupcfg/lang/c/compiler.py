# -*- encoding: utf-8 -*-

from tupcfg import Source, Target

from .. import compiler as base_compiler

class Compiler(base_compiler.Compiler):
    binary_env_varname = 'CC'


    def generate_precompiled_header(self, source, **kw):
        command = self._generate_precompiled_header(
            Source(source),
            precompiled_header = True,
            **kw
        )
        return self.build.add_target(Target(source + '.gch', command))

    def _generate_precompiled_header(self, source, **kw):
        raise Exception("Not implemented")
