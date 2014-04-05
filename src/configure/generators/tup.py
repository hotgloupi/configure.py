# -*- encoding: utf-8 -*-

from ..generator import Generator
from ..target import Target
from ..command import Command
from .. import path
from .. import build
from .. import tools

import os, sys, pipes

MAKEFILE_TEMPLATE = """
.PHONY:
.PHONY: all monitor

all: %(tup_config_dir)s %(dependencies)s
	@sh -c "cd %(root_dir)s && %(tup_bin)s upd %(build_dir)s" -j$(NUMJOBS)

%(tup_config_dir)s:
	@sh -c 'cd %(root_dir)s && %(tup_bin)s init'

monitor: %(tup_config_dir)s
	@sh -c 'export PATH=%(project_config_dir)s/tup:$$PATH; cd %(root_dir)s && %(tup_bin)s monitor -f -a'

"""

class Tup(Generator):

    def __init__(self, **kw):
        super(Tup, self).__init__(**kw)
        self.tupfiles = set()
        tup_bin = path.absolute(self.project.config_directory, 'tup/tup')
        if not path.exists(tup_bin):
            tup_bin = tools.find_binary('tup')
            assert path.exists(tup_bin)
        self.tup_bin = tup_bin


    #def __enter__(self):
    #    """Entering in a new build working directory."""
    #    p = path.join(self.working_directory, 'Tupfile')
    #    tools.debug(path.exists(p) and 'Updating' or 'Creating', p)
    #    self.tupfile = open(p, 'w')
    #    self.tupfiles.add(path.absolute(p))
    #    return self

    def begin(self):
        self.targets = {}
        self.directories = {}
        self.commands = {}
        self.seen = set()

    def __call__(self, node):
        if node in self.seen:
            return False
        self.seen.add(node)
        if isinstance(node, Target):
            if node.path not in self.targets:
                self.targets[node.path] = node
                self.directories.setdefault(node.dirname, []).append(node)
            assert self.targets[node.path] is node
        elif isinstance(node, Command):
            p = node.target.path
            assert self.commands.get(p, node) is node
            self.commands[p] = node

    def end(self):
        tupfiles = set()
        for dir, targets in self.directories.items():
            tupfile = path.join(dir, 'Tupfile')
            tupfiles.add(tupfile)
            with open(tupfile, 'w') as tupfile:
                for target in targets:
                    self.write_rule(dir, tupfile, target)
        for tupfile in tools.find_files(
            name = 'Tupfile',
            working_directory = self.build.directory):
            tupfile = path.absolute(tupfile)
            if tupfile not in tupfiles:
                tools.debug("Removing obsolete Tupfile", tupfile)
                os.unlink(tupfile)
        self.generate_makefile()

    def write_rule(self, dir, tupfile, target):
        def write(*args):
            args = args + ('\\',)
            print(*args, file = tupfile)

        command = self.commands.get(target.path)
        if command is None:
            return

        tools.debug("Add Tup rule for %s" % target)
        write(":")
        for input in command.target.dependencies:
            if input.path.startswith(self.project.directory):
                write('\t', input.relative_path(dir))

        write("|> ^o", command.action, target.basename, "^")
        write("%s -B %s" % (sys.executable, command.basename))
        write("|>", ' '.join(
            output.relative_path(dir)
            for output in command.outputs
        ))
        tupfile.write('\n')
        self.build.generate_commands([command], from_target = True)


    def generate_makefile(self):
        deps = []
        if self.build.dependencies:
            for dep in self.build.dependencies:
                for target in dep.targets:
                    deps.append(target.relative_path(self.build.directory))
        makefile_content = MAKEFILE_TEMPLATE % {
            'tup_config_dir': path.absolute(self.project.directory, '.tup'),
            'tup_bin': self.tup_bin,
            'root_dir': path.absolute(self.project.directory),
            'project_config_dir': path.absolute(self.project.config_directory),
            'dependencies': ' '.join(deps),
            'build_dir': path.relative(self.build.directory, start = self.project.directory)
        }

        cmd_str = lambda *cmd: ' '.join(map(pipes.quote, cmd))
        deps_dir = path.relative(
            self.build.dependencies_directory,
            start = self.build.directory,
        )
        for dep in deps:
            makefile_content += '\n\n%s:' % dep
            makefile_content += '\n\t@%s' % cmd_str(
                'make',
                '-C',
                deps_dir,
                path.relative(dep, start = deps_dir)
            )

        makefile = path.join(self.build.directory, 'Makefile')
        with open(makefile, 'w') as f:
            f.write(makefile_content)

        if not path.exists(path.join(self.project.directory, '.tup')):
            cmd = ['make', '-C', self.build.directory]
            print('Just run `%s`' % ' '.join(map(pipes.quote, cmd)))
