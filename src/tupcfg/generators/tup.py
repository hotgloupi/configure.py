# -*- encoding: utf-8 -*-

from ..generator import Generator
from .. import path
from .. import build
from .. import tools

import os, pipes

MAKEFILE_TEMPLATE = """
.PHONY:
.PHONY: all monitor

all: %(tup_config_dir)s %(dependencies)s
	@sh -c 'cd %(root_dir)s && %(tup_bin)s upd'

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


    def __enter__(self):
        """Entering in a new build working directory."""
        p = path.join(self.working_directory, 'Tupfile')
        tools.debug(path.exists(p) and 'Updating' or 'Creating', p)
        self.tupfile = open(p, 'w')
        self.tupfiles.add(path.absolute(p))
        return self

    def __exit__(self, type_, value, traceback):
        """Finalize a working directory."""
        self.tupfile.close()
        self.tupfile = None

    def apply_rule(self,
                   action=None,
                   command=None,
                   inputs=None,
                   additional_inputs=None,
                   outputs=None,
                   additional_outputs=None,
                   target=None):
        tools.debug("Add Tup rule for %s" % target)
        write = lambda *args: print(*(args + ('\\',)), file=self.tupfile)
        write(":")
        for input_ in inputs:
            #write('\t', input_.shell_string(**kw))
            write('\t', input_.relpath(target, self.build))
        for input_ in additional_inputs:
            #write('\t', input_.shell_string(**kw))
            write('\t', input_.relpath(target, self.build))
        write("|>")
        write("^", action, path.basename(str(target)), "^")
        for e in build.command(command, build = self.build, cwd = self.working_directory):
            write('\t', e)
        write("|>", target.shell_string(target, build=self.build))
        self.tupfile.write('\n')


    def close(self):
        for tupfile in tools.find_files(name = 'Tupfile',
                                        working_directory = self.build.directory):
            tupfile = path.absolute(tupfile)
            if tupfile not in self.tupfiles:
                tools.debug("Removing obsolete Tupfile", tupfile)
                os.unlink(tupfile)
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
        makefile_content = MAKEFILE_TEMPLATE % {
            'tup_config_dir': path.absolute(self.project.directory, '.tup'),
            'tup_bin': self.tup_bin,
            'root_dir': path.absolute(self.project.directory),
            'project_config_dir': path.absolute(self.project.config_directory),
            'dependencies': ' '.join(deps)
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
