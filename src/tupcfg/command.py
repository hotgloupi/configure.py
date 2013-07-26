# -*- encoding: utf-8 -*-

from . import path
from .node import Node
from .target import Target

import pipes

class Command(Node):

    @property
    def action(self):
        raise Exception("command action as to be overridden")


    def __init__(self, dependencies):
        super(Command, self).__init__(dependencies)

    def command(self, target=None, build=None):
        raise Exception("command property has to be overridden")

    def gen_command(self, shell_string=False, string=False, **kw):
        inputs, additional_inputs, outputs, additional_outputs = (
            self.__inputs(),
            [],
            [],
            [],
        )
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

    def __inputs(self):
        from .source import Source
        res = []
        def find_inputs(o):
            if isinstance(o, (Source, Target)):
                yield o
            #if isinstance(o, Node):
            #    for d in o.dependencies:
            #        for i in find_inputs(d):
            #            yield i
        for d in self.dependencies:
            res += list(find_inputs(d))
        return res

    def __gen_cmd(self, raw_cmd,
                  inputs, additional_inputs,
                  outputs, additional_outputs,
                  shell_string, string, **kw):
        args = (inputs, additional_inputs, outputs, additional_outputs,
                shell_string, string)
        import types
        if isinstance(raw_cmd, str):
            yield raw_cmd
            return
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
                        additional_inputs.extend(el.additional_inputs)
                        additional_outputs.extend(el.additional_outputs)
                    elif el not in inputs:
                        inputs.append(el)
                if shell_string:
                    for e in self.__gen_cmd(el.shell_string(**kw), *args, **kw):
                        yield e
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
        super().execute(target=target, build=build)
        build.emit_command(
            self.action,
            *self.gen_command(shell_string=False, target=target, build=build)
        )

    def __str__(self):
        return str(self.action)


class Simple(Command):
    def __init__(self, action, command, dependencies = []):
        super(Simple, self).__init__(dependencies)
        self.action = action
        self.__command = command

    def command(self, target, build):
        if callable(self.__command):
            return self.__command(target, build)
        else:
            return self.__command

class Shell(Command):
    action = None
    def __init__(self, action, command, working_directory = None, env = {}, dependencies = []):
        super(Shell, self).__init__(dependencies)
        self.action = action
        self.working_directory = working_directory
        self.env = env;
        self.__command = command

    @property
    def shell_command(self):
        cmd_str = lambda cmd: ' '.join(map(pipes.quote, map(str, cmd)))
        if self.working_directory is not None:
            cmd = cmd_str(['cd', self.working_directory])
            cmd += ' && ' + cmd_str(self.__command)
            res = ['sh', '-c', cmd]
        else:
            res = self.__command
        return ['%s=%s' % (k, v) for k, v in self.env.items()] + res

    def command(self, target=None, build=None):
        return self.shell_command

    def shell_string(self, build=None, cwd=None):
        return self.shell_command
