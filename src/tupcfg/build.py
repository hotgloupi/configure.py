# -*- encoding: utf-8 -*-

import os

from tupcfg import tools, path

class Build:
    def __init__(self, directory, root_directory='.'):
        self.directory = directory
        self.root_directory = root_directory
        self.targets = []
        self.tupfiles = set()

    def add_target(self, target):
        self.targets.append(target)
        return target

    def add_targets(self, *targets):
        for t in targets:
            if tools.isiterable(t):
                self.add_targets(*t)
            else:
                self.add_target(t)


    def dump(self, project, **kwargs):
        for t in self.targets:
            t.dump(build=self, **kwargs)

    def execute(self, project):
        generators = list(
            generator_class(project=project, build=self)
            for generator_class in project.generators
        )

        self.__commands = {}
        for t in self.targets:
            t.execute(build=self)
        for dir_, rules in self.__commands.items():
            if not path.exists(dir_):
                os.makedirs(dir_)
            tupfile = path.join(dir_, 'Tupfile')
            self.tupfiles.add(path.absolute(tupfile))
            tools.debug(path.exists(tupfile) and 'Updating' or 'Creating', tupfile)
            with open(tupfile, 'w') as f:
                self.__write_conf(dir_, f, rules)
            for generator in generators:
                with generator(working_directory=dir_) as gen:
                    for action, cmd, i, ai, o, ao, kw in rules:
                        gen.apply_rule(
                            action=action,
                            command=cmd,
                            inputs=i,
                            additional_inputs=ai,
                            outputs=o,
                            additional_ouputs=ao,
                            target=kw['target'],
                        )

        for generator in generators:
            generator.close()

    def cleanup(self):
        for tupfile in tools.glob('Tupfile', dir_=self.directory, recursive=True):
            tupfile = path.absolute(tupfile)
            if tupfile not in self.tupfiles:
                os.unlink(tupfile)

    def __write_conf(self, dir_, tupfile, rules):
        write = lambda *args: print(*(args + ('\\',)), file=tupfile)
        for action, cmd, i, ai, o, ao, kw in rules:
            write(":")
            for input_ in i:
                #write('\t', input_.shell_string(**kw))
                write('\t', input_.relpath(kw['target'], kw['build']))
            write("|>")
            if not tools.DEBUG:
                write("^", action, path.basename(str(kw['target'])), "^")
            for e in cmd:
                write('\t', e)
            write("|>", kw['target'].shell_string(**kw))
            tupfile.write('\n')


    def emit_command(self, action,
                     cmd,
                     inputs, additional_inputs,
                     outputs, additional_outputs,
                     kw):
        l = self.__commands.setdefault(
            path.dirname(kw['target'].path(kw['build'])),
            []
        )
        l.append((
            action, cmd,
            inputs, additional_inputs,
            outputs, additional_outputs,
            kw
        ))
