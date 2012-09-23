# -*- encoding: utf-8 -*-

from types import GeneratorType

class Node:

    def __init__(self, dependencies):
        if dependencies is None:
            dependencies = []
        if not isinstance(dependencies, (list, GeneratorType)):
            dependencies = [dependencies]
        self.dependencies = dependencies

    def dump(self, inc=0, **kwargs):
        if not self.dependencies:
            return
        for d in self.dependencies:
            kwargs['inc'] = inc
            d.dump(**kwargs)

    def execute(self, **kwargs):
        for d in self.dependencies:
            d.execute(**kwargs)

    def shell_string(self, **kwargs):
        return str(self)

