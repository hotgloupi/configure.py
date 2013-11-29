# -*- encoding: utf-8 -*-

import os
import sys
import types

from . import tools, path
from .filesystem import Filesystem
from .command import Command
from .target import Target
from .dependency import Dependency

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
                 generator_name: "generator name" = None,
                 save_generator = True,
                 dependencies_directory = 'dependencies'):
        self.directory = directory
        self.root_directory = project.directory
        self.dependencies_directory = path.join(directory, dependencies_directory)
        self.targets = []
        self.__dependencies = []
        self.__dependencies_build = None
        self.fs = Filesystem(self)
        self.project = project
        self.__seen_commands = None

        if not generator_name:
            generator_name = project.env.get(
                'BUILD_GENERATOR',
                default = 'Makefile'
            )
        elif save_generator:
            project.env.build_set('BUILD_GENERATOR', generator_name)

        if not generator_name:
            if tools.which('tup'):
                generator_name = 'Tup'
            else:
                tools.warning("Using makefile generator (tup not found)")
                generator_name = 'Makefile'

        from . import generators
        cls = getattr(generators, generator_name)
        self.generator = cls(project = project, build = self)
        self.__make_program = None
        self.__target_commands = {}

    @property
    def dependencies_build(self):
        if self.__dependencies_build is None:
            self.__dependencies_build = Build(
                self.project,
                self.dependencies_directory,
                'Makefile',
                save_generator = False,
            )
        return self.__dependencies_build

    @property
    def dependencies(self):
        return self.__dependencies

    def add_command(self, command):
        assert isinstance(command, Command)
        tools.debug("add command %s" % command)
        self.__target_commands.setdefault(command.target, []).append(command)
        return command

    def add_target(self, target):
        assert isinstance(target, Target)
        if target not in self.targets:
            tools.debug("add target %s" % target)
            self.targets.append(target)
        return target

    def add_targets(self, *targets):
        for t in targets:
            if tools.isiterable(t):
                self.add_targets(*t)
            else:
                self.add_target(t)

    def add_dependency(self, cls, *args, **kw):
        assert issubclass(cls, Dependency)
        tools.debug("add dependency", cls, args, kw)
        dependency = cls(self.dependencies_build, *args, **kw)
        self.__dependencies.append(dependency)
        self.dependencies_build.add_targets(dependency.targets)
        return dependency

    def dump(self):
        print("Build: ", self)
        class Visitor:
            def __init__(self):
                self.inc = 2
            def __call__(self, node):
                print(self.inc * ' ', repr(node))
                self.inc += 2
                for dep in node.dependencies:
                    self(dep)
                self.inc -= 2
        v = Visitor()
        for t in self.targets:
            v(t)

    def generate(self):
        tools.verbose("Entering build directory '%s'" % self.directory)

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        if self.__dependencies_build is not None:
            self.__dependencies_build.generate()
            self.__dependencies_build.cleanup()

        for target in self.targets:
            dirname = target.dirname
            if not os.path.exists(dirname):
                tools.debug("Creating directory", dirname)
                os.makedirs(dirname)
        with self.generator:
            for target in self.targets:
                target.visit(self.generator)

        tools.verbose("Leaving build directory '%s'" % self.directory)

    def cleanup(self):
        pass

    @property
    def make_program(self):
        if self.__make_program is None:
            self.__make_program = tools.find_binary(
                'make',
                self.project.env,
                'MAKE'
            )
        return self.__make_program

    def generate_commands(self,
                          commands,
                          force_working_directory = None,
                          from_target = False,
                          os_env = ('PATH',)):
        cmd_path = commands[0].path
        assert all(cmd.path == cmd_path for cmd in commands)

        script = "#!%s\n" % sys.executable
        script += '\n# -*- encoding: utf-8 -*-'
        script += '\nimport subprocess, sys, os'

        script += '\nos_env = {'
        for k, v in sorted((k, os.environ.get(k)) for k in os_env):
            script += '\n\t%s: %s,' % (repr(k), repr(v))
        script += '\n}'


        for cmd in commands:
            script += '\nenv = {}'
            script += '\nenv.update(os_env)'
            script += '\nenv.update({'
            for k, v in sorted(cmd.env.items()):
                script += '\n\t%s: %s,' % (repr(k), repr(v))
            script += '\n})'

            if force_working_directory is None:
                working_directory = cmd.working_directory
            else:
                working_directory = force_working_directory

            if not path.exists(working_directory):
                raise Exception("Command working directory %s does not exists" % working_directory)
            args = []
            for el in cmd.relative_command(working_directory):
                args.append(repr(el))
            script += '\nprint(%s, %s)' % (repr(cmd.action), repr(cmd.target.relative_path(working_directory)))
            script += '\nif os.environ.get("TUPCFG_DEBUG") or True:print(%s)' % ', '.join(repr(e) for e in cmd.command)
            script += '\nsys.exit('
            script += '\n\tsubprocess.call('
            script += '\n\t\t[\n\t\t\t%s\n\t\t],' % ',\n\t\t\t'.join(args)
            if from_target:
                script += '\n\t\tcwd = %s,' % repr(path.relative(working_directory, start = cmd.target.dirname))
            else:
                script += '\n\t\tcwd = %s,' % repr(working_directory)
            script += '\n\t\tenv = env,'
            script += '\n\t)'
            script += '\n)'
        script += '\n'

        if os.path.exists(cmd_path):
            with open(cmd_path, 'rb') as f:
                if f.read().decode('utf8') == script:
                    return
            is_new = False
            tools.status(
                "Update command",
                path.relative(cmd_path, start = self.project.directory)
            )
        else:
            is_new = True
            tools.status(
                "Create command",
                path.relative(cmd_path, start = self.project.directory)
            )
        with open(cmd_path, 'wb') as f:
            f.write(script.encode('utf8'))
        if is_new:
            os.chmod(cmd_path, 0o744)


