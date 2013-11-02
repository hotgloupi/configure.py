# -*- encoding: utf-8 -*-

import os
import pipes
import sys

from .. import path
from .. import tools

from ..generator import Generator
from ..target import Target
from ..command import Command

from ..build import command as build_command

class Makefile(Generator):

    def __init__(self, **kw):
        Generator.__init__(self, **kw)
        self.makefile = path.join(self.build.directory, 'Makefile')
        if path.exists(self.makefile):
            os.unlink(self.makefile)
        self.targets = {}
        self.commands = {}
        self.dependencies = set()

    def __call__(self, node):
        if isinstance(node, Target):
            assert self.targets.get(node.relative_path, node) is node
            if node in self.dependencies:
                pass
            elif node.relative_path in self.targets:
                self.targets.pop(node.relative_path)
                self.dependencies.add(node)
            else:
                self.targets[node.relative_path] = node
        elif isinstance(node, Command):
            self.commands.setdefault(node.target.relative_path, []).append(node)

    def close(self):
        cmd_str = lambda *cmd, **kw: kw.get('sep', ' ').join(map(pipes.quote, cmd))
        makefile = '# Generated makefile\n\n'
        makefile += 'PYTHON=%s\n' % sys.executable
        phony_rules = ['all', 'clean']
        makefile += '\n.PHONY:\n.PHONY: %s\n' % ' '.join(phony_rules)

        makefile += '\nall:'
        prev = len('all:')
        for target in sorted(self.targets.keys()):
            assert target not in self.dependencies
            makefile += (79 - prev) * ' ' + '\\\n  %s' % target
            prev = len(target) + 2

        deps = []
        if self.build.dependencies:
            for dep in self.build.dependencies:
                for target in dep.targets:
                    deps.append(target.relative_path)
            deps_dir = path.relative(
                self.build.dependencies_directory,
                start = self.build.directory,
            )
            for dep in deps:
                makefile += '\n\n%s:' % path.join(deps_dir, dep)
                makefile += '\n\t@%s' % cmd_str(
                    self.build.make_program,
                    '-C',
                    deps_dir,
                    dep
                )


        makefile += '\n\nclean:'
        for target in self.targets.keys():
            makefile += "\n\t@%s" % cmd_str('rm', '-fv', target)
        for target in self.dependencies:
            makefile += "\n\t@%s" % cmd_str('rm', '-fv', target.relative_path)

        makefile += '\n'

        for p, commands in self.commands.items():
            makefile += '\n\n%s:' % p
            commands = tools.unique(commands)
            prev = len(p) + 1
            for cmd in commands:
                #makefile += (79 - prev) * ' ' + '\\\n  %s' % cmd.relative_path
                #prev = len(cmd.relative_path) + 2
                for input in cmd.dependencies + cmd.target.dependencies:
                    p = input.make_relative_path(self.build.directory)
                    makefile += (79 - prev) * ' ' + '\\\n  %s' %  p
                    prev = len(p) + 2
            makefile += '\n\t@$(PYTHON) %s' % cmd_str(commands[0].relative_path)
            self.build.generate_commands(commands)


        makefile += '\n\n'
        with open(self.makefile, 'w') as f:
            f.write(makefile)

        return

        # XXX old stuff
        cmd_count = 0
        for depends_mode in (True, False):
            for target_path, target_list in self.targets.items():
                assert len(target_list) > 0
                target = target_list[0][0]
                target_str = str(target)
                header_dependency = bool(target_str.endswith('.depends.mk'))
                if (depends_mode and not header_dependency) or \
                   (not depends_mode and header_dependency):
                    continue

                inputs = sum((t[1] for t in target_list), [])
                additional_inputs = sum((t[2] for t in target_list), [])
                makefile += '# ------- %s:\n' % path.basename(target.path(self.build))
                makefile += '%s:' % target.relpath(self.build.directory, self.build)
                if self.build.dependencies:
                    makefile += ' %s' % ' '.join(deps)
                for i in inputs + additional_inputs:
                    makefile += ' %s' % i.relpath(self.build.directory, self.build)

                for idx, target_info in enumerate(target_list):
                    _, _, _, action, command = target_info
                    cmd_count += 1

                    timer_path = \
                            target.relpath(self.build.directory, self.build) + \
                            '.timer.%s' % cmd_count
                    makefile += '\n\t@%s' % cmd_str(
                        'sh', '-c', 'python -c "import time; print(time.time())" > %s' %
                        timer_path
                    )

                    # dump command
                    makefile += '\n\t%s' % cmd_str(*command)

                    # echo line
                    makefile += '\n\t@echo `%s`' % (
                         'python -c \'%s\'' % (
                             'import time; print("' +
                             '[%4f secs] ' +
                             '\033[0;34m' + action + '\033[0m ' +
                             '\033[0;31m' + target.relpath(self.project.directory, self.build) + '\033[0m' +
                             '" % (time.time() - float(open("' +
                             timer_path +
                             '").read())))'
                         )
                    )
                    makefile += '\n\t@%s' % cmd_str('rm', '-f', timer_path)
                makefile += '\n\n'

                if target_str.endswith('.depends.mk'):
                    makefile += 'include %s\n\n' % target_str

        with open(self.makefile, 'w') as f:
            f.write(makefile)

