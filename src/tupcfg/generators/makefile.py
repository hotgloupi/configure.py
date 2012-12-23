# -*- encoding: utf-8 -*-

import os
import pipes

from .. import path

from ..generator import Generator
from ..target import Target

class Makefile(Generator):

    def __init__(self, **kw):
        Generator.__init__(self, **kw)
        self.makefile = path.join(self.build.directory, 'Makefile.generated')
        if path.exists(self.makefile):
            os.unlink(self.makefile)
        self.targets = {}
        self.dependencies = {}

    def apply_rule(self,
                   action=None,
                   command=None,
                   inputs=None,
                   additional_inputs=None,
                   outputs=None,
                   additional_ouputs=None,
                   target=None):
        target_path = target.relpath(self.build.directory, self.build)
        assert target_path not in self.targets
        self.targets[target_path] = (target, inputs, action, command)
        for i in inputs:
            if not isinstance(i, Target):
                continue
            i_path = i.relpath(self.build.directory, self.build)
            self.dependencies[i_path] = i

    def close(self):
        cmd_str = lambda *cmd: ' '.join(map(pipes.quote, cmd))

        makefile = '.PHONY:\n.PHONY: all clean\nall: '
        for target in self.targets.keys():
            if target not in self.dependencies:
                makefile += ' %s' % target

        makefile += '\n\nclean:'
        for target in self.targets.keys():
            p = path.absolute(self.build.directory, target)
            makefile += '\n\t@%s' % cmd_str(
                'sh', '-c', cmd_str(
                    'echo',
                    '\033[0;34mRemove\033[0m ' +
                    '\033[0;31m' + path.relative(p, start=self.project.directory) + '\033[0m'
                )
            )
            makefile += "\n\t@%s" % cmd_str('rm', '-f', p)

        makefile += '\n\n'

        for target_path, infos in self.targets.items():
            target, inputs, action, command = infos
            makefile += '%s:' % target
            for i in inputs:
                makefile += ' %s' % i.relpath(self.build.directory, self.build)
            makefile += '\n\t@%s' % cmd_str(
                'sh', '-c', cmd_str(
                    'echo',
                    '\033[0;34m' + action + '\033[0m ' +
                    '\033[0;31m' + target.relpath(self.project.directory, self.build) + '\033[0m'
                )
            )
            working_directory = path.dirname(target_path)
            makefile += '\n\t@%s' % cmd_str(
                'sh', '-c', cmd_str('cd', working_directory) + ' && ' + cmd_str(*command)
            )
            makefile += '\n\n'

        with open(self.makefile, 'w') as f:
            f.write(makefile)
