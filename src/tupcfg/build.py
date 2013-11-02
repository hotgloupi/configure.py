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

    def generate_commands(self, commands):
        path = commands[0].path
        assert all(cmd.path == path for cmd in commands)
        script = "#!%s\n" % sys.executable
        script += '\n# -*- encoding: utf-8 -*-'
        script += '\nimport subprocess, sys, os'
        for cmd in commands:
            if not os.path.exists(cmd.working_directory):
                raise Exception("Command working directory %s does not exists" % cmd.working_directory)
            args = []
            for el in cmd.command:
                args.append('"""%s"""' % el)
            env = []
            for item in cmd.env.items():
                env.append('"""%s""": """%s"""' % item)
            env.append('"PATH": os.environ["PATH"]')
            script += '\nprint("""%s %s""")' % (cmd.action, cmd.target.relative_path)
            script += '\nif os.environ.get("TUPCFG_DEBUG"):print("""%s""")' % ' '.join(cmd.command)
            script += '\nsys.exit(subprocess.call(\n[\n\t%s\n],\ncwd = """%s""",\nenv = {\n\t%s\n}))' % (
                ',\n\t'.join(args),
                cmd.working_directory,
                ',\n\t'.join(env)
            )
        script += '\n'


        if os.path.exists(path):
            with open(path, 'rb') as f:
                if f.read().decode('utf8') == script:
                    return
        else:
            is_new = True
        with open(path, 'wb') as f:
            f.write(script.encode('utf8'))
        if is_new:
            os.chmod(path, 0o744)
