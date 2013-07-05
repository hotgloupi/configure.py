# -*- encoding: utf-8 -*-

from tupcfg import Source, Target

from tupcfg.compiler import Compiler as BaseCompiler

class Compiler(BaseCompiler):
    binary_env_varname = 'CC'

    def build_object(self, src, **kw):
        target = super(Compiler, self).build_object(src, **kw)
        pchs = kw.get('precompiled_headers', []) + self.precompiled_headers
        target.additional_inputs.extend(pchs)
        return target

    def generate_precompiled_header(self, source, force_include = False, **kw):
        cpy = self.build.fs.copy(source)
        command = self._generate_precompiled_header(
            cpy,
            precompiled_header = True,
            **kw
        )
        target = Target(source + '.gch', command)
        target.source = command.source
        target.force_include = force_include
        return self.build.add_target(target)

    def _generate_precompiled_header(self, source, **kw):
        raise Exception("Not implemented")
