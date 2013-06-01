# -*- encoding: utf-8 -*-

from tupcfg import Source, Target

from tupcfg.compiler import Compiler as BaseCompiler

class Compiler(BaseCompiler):
    binary_env_varname = 'CC'

    def build_object(self, src, **kw):
        target = super(Compiler, self).build_object(src, **kw)
        pchs = kw.get('precompiled_headers', [])
        for pch in pchs:
            print("ADD pch !")
            target.additional_inputs.append(pch)
        return target

    def generate_precompiled_header(self, source, **kw):
        command = self._generate_precompiled_header(
            Source(source),
            precompiled_header = True,
            **kw
        )
        return self.build.add_target(Target(source + '.gch', command))

    def _generate_precompiled_header(self, source, **kw):
        raise Exception("Not implemented")
