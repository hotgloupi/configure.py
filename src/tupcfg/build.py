# -*- encoding: utf-8 -*-

import os
import types

from . import tools, path
from .filesystem import Filesystem

def command(cmd, build=None, cwd=None):
    """Yield a build command relative to cwd if provided or build.directory"""
    return list(_command(cmd, build=build, cwd=cwd))

def _command(cmd, build=None, cwd=None):
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
    def __init__(self,
                 project: "The project instance",
                 directory: "The build directory",
                 generator_names: "A list of generator names",
                 save_generator = True,
                 dependencies_directory = 'dependencies'):
        self.directory = directory
        self.root_directory = project.directory
        self.dependencies_directory = path.join(directory, dependencies_directory)
        self.targets = []
        self.dependencies = []
        self.fs = Filesystem(self)
        self.project = project
        # initialized by execute()
        self.__commands = None
        self.__seen_commands = None

        if not generator_names:
            generator_names = project.env.get(
                'BUILD_GENERATORS',
                type = list,
                default = []
            )
        elif save_generator:
            project.env.build_set('BUILD_GENERATORS', generator_names)

        if not generator_names:
            if tools.which('tup'):
                generator_names = ['Tup']
            else:
                tools.warning("Using makefile generator (tup not found)")
                generator_names = ['Makefile']

        assert len(generator_names)

        self.generators = []
        from . import generators as _generators
        for gen in generator_names:
            cls = getattr(_generators, gen)
            self.generators.append(cls(project = project, build = self))
        assert len(self.generators)

    def add_target(self, target):
        if target not in self.targets:
            tools.debug("add target {%s}/%s" % (self.directory, target))
            self.targets.append(target)
        return target

    def add_targets(self, *targets):
        for t in targets:
            if tools.isiterable(t):
                self.add_targets(*t)
            else:
                self.add_target(t)

    def add_dependency(self, dependency):
        self.dependencies.append(dependency)
        return dependency

    def add_dependencies(self, *dependencies):
        for dep in dependencies:
            if tools.isiterable(dep):
                self.add_targets(*dep)
            else:
                self.add_target(dep)

    def dump(self, project, **kwargs):
        for t in self.targets:
            t.dump(build=self, **kwargs)

    def execute(self, project):
        tools.verbose("Entering build directory '%s'" % self.directory)

        if self.dependencies:
            deps_build = Build(
                project,
                self.dependencies_directory,
                ['Makefile'],
                save_generator = False,
            )
            for dep in self.dependencies:
                dep.set_build(deps_build)
                deps_build.add_targets(dep.targets)
            deps_build.execute(project)
            deps_build.cleanup()

        self.__commands = {}
        self.__seen_commands = set()
        for t in self.targets:
            tools.debug("Exectuting {%s}/%s" % (self.directory, t))
            t.execute(build=self)
        for dir_, rules in self.__commands.items():
            if not path.exists(dir_):
                os.makedirs(dir_)
            for generator in self.generators:
                self.generator = generator
                with generator(working_directory=dir_) as gen:
                    tools.verbose(
                        " -> Working on", path.relative(dir_, start = self.directory)
                    )
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

        for generator in self.generators:
            generator.close()
        tools.verbose("Leaving build directory '%s'" % self.directory)

    def cleanup(self):
        pass

    def emit_command(self, action,
                     cmd,
                     inputs, additional_inputs,
                     outputs, additional_outputs,
                     kw):
        target = kw['target']
        target_dir = path.dirname(target.path(kw['build']))
        cmd_object = '-'.join(str(e) for e in command(cmd, build = self))
        if cmd_object in self.__seen_commands:
            tools.debug("Ignoring {%s}/%s command %s" % (self.directory, target, cmd))
            return
        self.__seen_commands.add(cmd_object)

        tools.debug("Adding {%s}/%s command %s" % (self.directory, target, cmd))
        self.__commands.setdefault(target_dir, []).append(
            (
                action, cmd,
                inputs, additional_inputs,
                outputs, additional_outputs,
                kw
            )
        )
