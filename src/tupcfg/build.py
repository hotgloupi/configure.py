# -*- encoding: utf-8 -*-

import os

class Build:
    def __init__(self, directory, root_directory='.'):
        self.directory = directory
        self.root_directory = root_directory
        self.targets = set()

    def add_target(self, target):
        self.targets.add(target)
        return self


    def dump(self, project, **kwargs):
        for t in self.targets:
            t.dump(build=self, project=project, **kwargs)

    def execute(self, project, **kwargs):
        self.__commands = {}
        for t in self.targets:
            t.execute(build=self, project=project, **kwargs)
        for dir_, rules in self.__commands.items():
            if not os.path.exists(dir_):
                os.makedirs(dir_)
            with open(os.path.join(dir_, 'Tupfile'), 'w') as f:
                print("Writing", os.path.join(dir_, 'Tupfile'))
                self.__write_conf(dir_, f, rules)

    def __write_conf(self, dir_, tupfile, rules):
        write = lambda *args: print(*(args + ('\\',)), file=tupfile)
        for inputs, cmd, kw in rules:
            write(":")
            for i in inputs:
                write('\t', i.shell_string(**kw))
            write("|>", *cmd)
            write("|>", kw['target'].shell_string(**kw))
            tupfile.write('\n')


    def emit_command(self, cmd_, **kw):
        b, t = kw['build'], kw['target']
        inputs = []
        cmd = []
        for e in cmd_:
            if isinstance(e, str):
                cmd.append(e)
                continue
            cmd.append(e.shell_string(**kw))
            if e != t:
                inputs.append(e)

        directory = t.directory(b)
        l = self.__commands.setdefault(directory, [])
        l.append((inputs, cmd, kw))
