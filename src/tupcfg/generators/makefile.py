# -*- encoding: utf-8 -*-

import os
import pipes

from .. import path

from ..generator import Generator
from ..target import Target

from ..build import command as build_command

class Makefile(Generator):

    def __init__(self, **kw):
        Generator.__init__(self, **kw)
        self.makefile = path.join(self.build.directory, 'Makefile')
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
        target_list = self.targets.setdefault(target_path, []).append(
            (
                target, inputs, additional_inputs, action,
                list(build_command(command, build=self.build))
            )
        )
        for i in inputs:
            if not isinstance(i, Target):
                continue
            i_path = i.relpath(self.build.directory, self.build)
            self.dependencies[i_path] = i

    def close(self):
        cmd_str = lambda *cmd: ' '.join(map(pipes.quote, cmd))

        phony_rules = ['all', 'clean']
        makefile = '.PHONY:\n.PHONY: %s\n' % ' '.join(phony_rules)


        makefile += '\nall:'
        for target in self.targets.keys():
            if target not in self.dependencies:
                makefile += ' %s' % target

        deps = []
        if self.build.dependencies:
            for dep in self.build.dependencies:
                for target in dep.targets:
                    deps.append(
                        path.relative(
                            target.path(dep.resolved_build),
                            start = self.build.directory
                        )
                    )
            deps_dir = path.relative(
                self.build.dependencies_directory,
                start = self.build.directory,
            )
            for dep in deps:
                makefile += '\n\n%s:' % dep
                makefile += '\n\t@%s' % cmd_str(
                    'make',
                    '-C',
                    deps_dir,
                    path.relative(dep, start = deps_dir)
                )


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

        for depends_mode in (True, False):
            for target_path, infos in self.targets.items():
                target, inputs, additional_inputs, action, command = infos
                target_str = str(target)
                if (depends_mode and not target_str.endswith('.depends.mk')) or \
                    not depends_mode and target_str.endswith('.depends.mk'):
                    continue
                makefile += '%s:' % target
                if self.build.dependencies:
                    makefile += ' %s' % ' '.join(deps)
                for i in inputs + additional_inputs:
                    makefile += ' %s' % i.relpath(self.build.directory, self.build)

                makefile += '\n\t@%s' % cmd_str(
                    'sh', '-c', cmd_str(
                        'echo',
                        '\033[0;34m' + action + '\033[0m ' +
                        '\033[0;31m' + target.relpath(self.project.directory, self.build) + '\033[0m'
                    )
                )
                working_directory = path.dirname(target_path)
                makefile += '\n\t%s' % cmd_str(*command)
                makefile += '\n\n'

                if target_str.endswith('.depends.mk'):
                    makefile += 'include %s\n\n' % target_str

        with open(self.makefile, 'w') as f:
            f.write(makefile)

