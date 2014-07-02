import copy

from . import Dependency
from ..command import Command
from ..target import Target
from .. import platform, path

class AutotoolsDependency(Dependency):

    def __init__(self,
                 build,
                 name,
                 source_directory,
                 compiler,
                 libraries = [],
                 configure_interpreter = 'sh',
                 configure_script = 'configure',
                 configure_target = 'Makefile',
                 configure_env = {},
                 configure_arguments = [],
                 configure_variables = {},
                 os_env = []):

        super().__init__(
            build = build,
            name = name,
            source_directory = source_directory,
            libraries = libraries,
            compiler = compiler,
        )
        self.configure_interpreter = configure_interpreter
        self.configure_script = configure_script
        self.configure_target = configure_target
        self.configure_env = copy.copy(configure_env)
        self.configure_arguments = configure_arguments
        self.configure_variables = configure_variables
        self.os_env = os_env

        command = []
        if self.configure_interpreter:
            command.append(self.configure_interpreter)
        command.append(self.absolute_source_path(self.configure_script))
        command.append('--prefix=%s' % self.install_directory)

        if self.compiler.binary_env_varname not in self.configure_env:
            self.configure_env[self.compiler.binary_env_varname] = self.compiler.binary
        command.extend(self.configure_arguments)
        command.extend('%s=%s' % i for i in self.configure_variables.items())

        configure_target = Command(
            "Configure %s" % self.name,
            target = Target(
                self.build,
                self.build_path('build', self.configure_target)
            ),
            command = command,
            working_directory = self.build_directory,
            os_env = self.os_env,
            env = self.configure_env,
        ).target

        command = ['make', 'install']
        self.targets = [
            Command(
                "Building %s" % self.name,
                target = self.target_libraries[0],
                additional_outputs = self.target_libraries[1:],
                command = command,
                working_directory = self.build_path('build'),
                inputs = [configure_target],
                os_env = self.os_env,
            ).target
        ]

