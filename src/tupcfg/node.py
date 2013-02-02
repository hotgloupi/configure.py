# -*- encoding: utf-8 -*-

from types import GeneratorType

class Node:

    def __init__(self, dependencies):
        if dependencies is None:
            dependencies = []
        if not isinstance(dependencies, (list, GeneratorType)):
            dependencies = [dependencies]
        self.dependencies = dependencies

    def dump(self, inc=0, target=None, build=None):
        if not self.dependencies:
            return
        for d in self.dependencies:
            d.dump(inc=inc + 2, target=target, build=build)

    def execute(self, target=None, build=None):
        for d in self.dependencies:
            d.execute(target=target, build=build)

    def shell_string(self, target=None, build=None):
        return str(self)

