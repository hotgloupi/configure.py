# -*- encoding: utf-8 -*-

import os
import types

from tupcfg import tools, path

def command(cmd, build=None, cwd=None):
    return list(_command(cmd, build=build, cwd=cwd))

def _command(cmd, build=None, cwd=None):
    pass
    """Yield a build command relative to cwd if provided or build.directory"""
    assert build is not None
    if cwd is None:
        cwd = build.directory
    if isinstance(cmd, str):
        yield cmd
        return
    for el in cmd:
        if isinstance(el, str):
            yield el
        elif isinstance(el, (list, tuple, types.GeneratorType)):
            for sub_el in _command(el, build=build, cwd=cwd):
                yield sub_el
        else:
            res =  _command(
                el.shell_string(build=build, cwd=cwd),
                build = build,
                cwd = cwd
            )
            for sub_el in res:
                yield sub_el


class Build:
    def __init__(self, directory, root_directory='.'):
        self.directory = directory
        self.root_directory = root_directory
        self.targets = []

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
        pass

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
