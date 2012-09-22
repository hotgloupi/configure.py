# -*- encoding: utf-8 -*-

from .node import Node

class Command(Node):

    def __init__(self, dependencies):
        super(Command, self).__init__(dependencies)

    @property
    def command(self, **kwargs):
        raise Exception("command property has to be overridden")

    def dump(self, inc=0, **kw):
        target = kw.get('target')
        if target is None:
            raise Exception("Cannot dump a command without target")
        cmd = self.command(**kw)
        if isinstance(cmd, list):
            cmd = ' '.join(
                (isinstance(el, str) and [el] or [
                    el.shell_string(**kw)
                ])[0]
                for el in cmd
            )
        print(
            ' ' * inc,
            kw['target'].directory(kw['build']) + ':',
            cmd
        )
        kw['inc'] = inc + 2
        super(Command, self).dump(**kw)

    def execute(self, **kw):
        super(Command, self).execute(**kw)
        kw['build'].emit_command(self.command(**kw), **kw)


