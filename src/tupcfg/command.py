# -*- encoding: utf-8 -*-

from .node import Node
from . import path

class Command(Node):

    @property
    def action(self):
        raise Exception("command action as to be overridden")


    def __init__(self, dependencies):
        super(Command, self).__init__(dependencies)

    def command(self, target=None, build=None):
        raise Exception("command property has to be overridden")

    def gen_command(self, shell_string=False, string=False, **kw):
        inputs, additional_inputs, outputs, additional_outputs = [], [], [], []
        cmd = list(self.__gen_cmd(
            self.command(**kw),
            inputs,
            additional_inputs,
            outputs,
            additional_outputs,
            shell_string,
            string,
            **kw
        ))
        return (cmd, inputs, additional_inputs, outputs, additional_outputs, kw)

    def __gen_cmd(self, raw_cmd,
                  inputs, additional_inputs,
                  outputs, additional_outputs,
                  shell_string, string, **kw):
        args = (inputs, additional_inputs, outputs, additional_outputs,
                shell_string, string)
        import types
        for el in raw_cmd:
            if isinstance(el, str):
                yield el
                continue
            if isinstance(el, (list, types.GeneratorType)):
                for sub_el in self.__gen_cmd(el, *args, **kw):
                    yield sub_el
            else:
                if isinstance(el, Node):
                    if el == kw['target']:
                        outputs.append(el)
                    else:
                        inputs.append(el)

                if shell_string:
                    yield el.shell_string(**kw)
                elif string:
                    yield str(el)
                else:
                    yield el

    def dump(self, inc=0, **kw):
        target = kw.get('target')
        if target is None:
            raise Exception("Cannot dump a command without target")
        cmd, i, ai, o, ao, cmd_kw = self.gen_command(string=True, **kw)
        print(
            ' ' * inc,
            path.dirname(kw['target'].path(kw['build'])) + ':',
            '\n\t' + ' ' * inc, ' * inputs:', ' '.join(repr(e) for e in i),
            '\n\t' + ' ' * inc, ' * additional inputs:', ' '.join(repr(e) for e in ai),
            '\n\t' + ' ' * inc, ' * outputs:', ' '.join(repr(e) for e in o),
            '\n\t' + ' ' * inc, ' * additional outputs:', ' '.join(repr(e) for e in ao),
            '\n\t' + ' ' * inc, ' * kwargs:', ', '.join(
                ("%s=%s") % it for it in cmd_kw.items()
            ),
            '\n' + ' ' * inc, '->', ' '.join(cmd)
        )
        kw['inc'] = inc + 2
        super(Command, self).dump(**kw)

    def execute(self, target=None, build=None):
        assert build is not None
        super(Command, self).execute(target=target, build=build)
        build.emit_command(
            self.action,
            *self.gen_command(shell_string=True, target=target, build=build)
        )


