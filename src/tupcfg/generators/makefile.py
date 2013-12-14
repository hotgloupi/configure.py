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
            p = node.relative_path(self.build.directory)
            assert self.targets.get(p, node) is node
            if node in self.dependencies:
                pass
            elif node.relative_path(p) in self.targets:
                self.targets.pop(p)
                self.dependencies.add(node)
            else:
                self.targets[p] = node
        elif isinstance(node, Command):
            self.commands.setdefault(
                node.target.relative_path(self.build.directory),
                []
            ).append(node)

    def end(self):
        cmd_str = lambda *cmd, **kw: kw.get('sep', ' ').join(map(pipes.quote, cmd))
        makefile = '# Generated makefile\n\n'
        makefile += 'PYTHON=%s\n' % sys.executable
        makefile += 'MAKE_DEPENDS=$(PYTHON) %s --root %s --makefile' % (
            path.absolute(path.dirname(__file__), 'find_dependencies.py'),
            '.'
        )
        phony_rules = ['all', 'clean']
        makefile += '\n.PHONY:\n.PHONY: %s\n' % ' '.join(phony_rules)

        #######################################################################
        # Find C/C++ header dependencies
        from tupcfg.lang.c.compiler import CSource
        from tupcfg.lang.cxx.compiler import CXXSource
        from tupcfg.compiler import IncludeDirectory

        found_c_sources = {}
        target_sources = {}
        for p, commands in self.commands.items():
            for cmd in commands:
                for input in cmd.target.dependencies:
                    if input in found_c_sources:
                        continue
                    if isinstance(input, (CSource, CXXSource)):
                        found_c_sources[input] = list(cmd.find_instances(IncludeDirectory))
                        target_sources.setdefault(cmd.target, set()).add(input)

        #######################################################################
        # Dump 'all' rule
        makefile += '\n\nall:'
        prev = len('all:')
        for target in sorted(self.targets.keys()):
            assert target not in self.dependencies
            makefile += (78 - prev) * ' ' + '\\\n  %s' % target
            prev = len(target) + 2
        for target in target_sources.keys():
            depend = target.relative_path(self.build.directory) + '.depend.mk'
            makefile += (78 - prev) * ' ' + '\\\n  %s' % depend
            prev = len(depend) + 2

        #######################################################################
        # Dump 'clean' rule
        makefile += '\n\nclean:'
        for target in self.targets.keys():
            makefile += "\n\t@%s" % cmd_str('rm', '-fv', target)
        for target in self.dependencies:
            makefile += "\n\t@%s" % cmd_str('rm', '-fv', target.relative_path(self.build.directory))

        # XXX Dependencies are always built ...
        for target in target_sources.keys():
            depend = target.relative_path(self.build.directory) + '.depend.mk'
            makefile += "\n\t@%s" % cmd_str('rm', '-fv', depend)
        count = len(self.targets) + len(self.dependencies) #+ len(target_sources)
        makefile += '\n\t@sh -c "echo \'%s targets removed\'"' % count


        #######################################################################
        # Dump dependencies rules
        deps = []
        if self.build.dependencies:
            for dep in self.build.dependencies:
                for target in dep.targets:
                    deps.append(target.relative_path(self.build.directory))
            deps_dir = path.relative(
                self.build.dependencies_directory,
                start = self.build.directory,
            )
            for dep in deps:
                makefile += '\n\n%s:' % dep
                makefile += '\n\t@%s' % cmd_str(
                    self.build.make_program,
                    '-C',
                    deps_dir,
                    path.relative(dep, start = deps_dir),
                )

        #######################################################################
        # Dump C/C++ header dependencies rules
        for target, sources in target_sources.items():
            target_path = target.relative_path(self.build.directory)
            depend = target_path + '.depend.mk'
            makefile += '\n\n%s:' % depend
            prev = len(depend) + 1
            for input in sources:
                p = input.relative_path(self.build.directory)
                makefile += (78 - prev) * ' ' + '\\\n  %s' %  p
                prev = len(p) + 2
            cmd = '@$(MAKE_DEPENDS) -o %s -t %s' % (depend, target_path)
            makefile += '\n\t' + cmd
            prev = len(cmd) + 8
            for input in sources:
                p = input.relative_path(self.build.directory)
                makefile += (78 - prev) * ' ' + '\\\n\t  %s' %  p
                prev = len(p) + 8 + 2
                for dir in found_c_sources[input]:
                    p = dir.relative_path(self.build.directory)
                    makefile += (78 - prev) * ' ' + '\\\n\t  -I %s' %  p
                    prev = len(p) + 8 + 2 + 3
            makefile += '\n\n-include %s' % depend
            #makefile += '\n%s: %s' % (target_path, depend)

        #######################################################################
        # Dump commands
        for p, commands in self.commands.items():
            outputs = tools.unique(
                map(
                    lambda n: n.relative_path(),
                    sum((cmd.outputs for cmd in commands), ())
                )
            )
            assert len(outputs)
            makefile += '\n\n%s:' % outputs[0]
            prev = len(p) + 1
            commands = tools.unique(commands)
            for cmd in commands:
                #makefile += (79 - prev) * ' ' + '\\\n  %s' % cmd.relative_path
                #prev = len(cmd.relative_path) + 2
                for input in cmd.dependencies + cmd.target.dependencies:
                    p = input.relative_path(self.build.directory)
                    makefile += (78 - prev) * ' ' + '\\\n  %s' %  p
                    prev = len(p) + 2
            makefile += '\n\t@$(PYTHON) %s' % cmd_str(commands[0].relative_path(self.build.directory))
            self.build.generate_commands(commands)

            if len(outputs) > 1:
                for o in outputs[1:]:
                    makefile += "\n\n%s: %s" % (o, outputs[0])


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

