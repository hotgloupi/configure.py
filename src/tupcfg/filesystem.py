# -*- encoding: utf-8 -*-

if __name__ == '__main__':
    import os
    def generate_file(path, content):
        import json
        content = json.loads(content)
        if os.path.exists(path):
            with open(path, 'r') as f:
                old_content = f.read()
        else:
            old_content = None
        if content != old_content:
            with open(path, 'w') as f:
                f.write(content)
        print("Generated file:", path)
    import sys
    print("Module filesystem called with:", sys.argv)
    actions = {
        'generate_file': generate_file,
    }
    actions[sys.argv[1]](*sys.argv[2:])
    sys.exit(0)

from .command import Command
from .source import Source
from .target import Target

from . import path

class GenerateCommand(Command):
    @property
    def action(self):
        return "Generating file"
    def command(self, target = None, build = None):
        from tupcfg.tools import python_command
        import json
        return python_command(
            file = path.absolute(__file__),
            args = [
                'generate_file',
                target.path(build = build),
                json.dumps(target.content(target = target, build = build))
            ]
        )

class Generate(Target):
    def __init__(self, name, content = None, dependencies = [], lazy = True):
        if lazy:
            dependencies.append(GenerateCommand(dependencies = []))
        super().__init__(name, dependencies)
        self.content = content
        self.created = False
        self.lazy = lazy

    def execute(self, target = None, build = None):
        super(Target, self).execute(target=self, build=build)
        if not self.lazy:
            self._execute(target = self, build = build)

    def _execute(self, target = None, build = None):
        if not self.created:
            p = self.path(build)
            print("Generate", p)
            if path.exists(p):
                with open(p, 'r') as f:
                    old_content = f.read()
            else:
                if not path.is_directory(path.dirname(p)):
                    path.make_path(path.dirname(p))
                old_content = None
            content = self.content(target = target, build = build)
            if content != old_content:
                with open(p, 'w') as f:
                    f.write(content)
            self.created = True

class Copy(Command):
    @property
    def action(self):
        return "Copying %s to" % self.dependencies[0]
    def command(self, **kw):
        return ['cp', self.dependencies, kw['target']]

class Filesystem:
    """Filesystem operations on a build.
    """
    def __init__(self, build):
        self.build = build

    def generate(self, dst, content_gen = None, lazy = True):
        """Create a file with generated content.

        The content generator must be callable with target and build arguments,
        and return the string. In non lazy mode the targetted file is built by
        tupcfg at configure time, otherwise the file will be created at compile
        time. Prefer the lazy mode when possible, letting the build system in
        charge to check file's freshness.
        """
        return Generate(dst, content = content_gen, lazy = lazy)

    def copy(self, src, dest = None, dest_dir = None):
        """
        """
        if dest is None:
            if dest_dir is not None:
                dest = path.join(dest_dir, path.basename(str(src)))
            else:
                dest = src
        if not isinstance(src, Target):
            src = Source(src)

        return self.build.add_target(
            Target(dest, Copy(src))
        )
