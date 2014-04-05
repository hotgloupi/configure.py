# -*- encoding: utf-8 -*-

from .node import Node
from .source import Source
from .target import Target
from . import tools
from . import path as PATH

import pipes

class Command(Source):

    __slots__ = (
        '__action',
        '__command',
        '__working_directory',
        '__os_env',
        '__env',
        '__outputs',
    )

    def __init__(self,
                 action,
                 command,
                 target,
                 inputs = tuple(),
                 additional_outputs = tuple(),
                 working_directory = None,
                 os_env = [],
                 env = {}):
        self.__action = action
        self.__command = list(self.__make_flat(command))

        if working_directory is None:
            working_directory = target.build.directory
        elif not PATH.is_absolute(working_directory):
            working_directory = PATH.absolute(target.build.directory, working_directory)
        self.__working_directory = PATH.absolute(working_directory)

        assert isinstance(os_env, list)
        self.__os_env = os_env

        assert isinstance(env, dict)
        self.__env = env

        assert isinstance(target, Target)
        self.__outputs = (target,) + tuple(additional_outputs)

        target.dependencies.extend(inputs)
        seen = set(el.path for el in target.dependencies)
        seen.update(el.path for el in self.__outputs)
        target.dependencies.extend(
            input for input in self.__find_other_inputs(self.__command, seen)
        )
        target.dependencies.append(self)

        super().__init__(
            target.build,
            target.path + ".command",
        )
        self.build.add_command(self)

    @property
    def action(self):
        return self.__action

    def _root_directory(self):
        return self.build.directory

    @property
    def working_directory(self):
        return self.__working_directory

    @property
    def outputs(self):
        return self.__outputs

    @property
    def original_command(self):
        return self.__command

    @property
    def command(self):
        return self.relative_command(self.working_directory)

    def relative_command(self, working_directory):
        return list(self.__parse_command(self.__command, working_directory))

    @property
    def target(self):
        return self.__outputs[0]

    @property
    def os_env(self):
        return self.__os_env

    @property
    def env(self):
        return self.__env

    def __str__(self):
        return str(self.action)

    def __repr__(self):
        return '<Command %s: %s>' % (self.action, self.relative_command(self.build.directory))

    def __parse_command(self, cmd, working_directory):
        for el in cmd:
            if isinstance(el, str):
                yield el
            elif isinstance(el, Node):
                for subel in self.__parse_command(el.shell(working_directory), working_directory):
                    yield subel
            else:
                raise Exception("Unknown command element: %s" % el)

    def find_instances(self, type):
        for el in self.__command:
            if isinstance(el, type):
                yield el

    def __make_flat(self, cmd):
        for el in cmd:
            if tools.isiterable(el):
                for subel in self.__make_flat(el):
                    yield subel
            else:
                yield el

    def __find_other_inputs(self, cmd, found):
        for el in cmd:
            if isinstance(el, (str, Command)):
                continue
            elif el.path in found or el.is_directory:
                continue
            elif isinstance(el, Node):
                found.add(el.path)
                yield el
            else:
                raise Exception("Unknown command element: %s" % el)
