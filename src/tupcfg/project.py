# -*- encoding: utf-8 -*-

import os
import re
import sys

from . import tools
from . import templates

class Env:
    var_re = re.compile('^[A-Z][A-Z0-9_]*$')
    def __init__(self, project, conf={}):
        self._dict = conf
        self.project = project

    def __execute_command(self, cmd):
        return None

    def __getitem__(self, key):
        var = self._dict.get(key)
        if var is None:
            cmd = self._dict.get(key + '_CMD')
            if cmd is None:
                raise KeyError("both %s and %s_CMD are None" % (key, key))
            var = self.__execute_command(cmd)
            if var is None:
                raise ValueError("Result of command %s_CMD is None" % key)
            self._dict[key] = var
        return var

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getattr__(self, key):
        return self.__getitem__(key)


    def __iter__(self):
        for item in self._dict.items():
            yield item

class Project:

    class NeedUserEdit(Exception):
        """Raised if the configuration was generated."""
        pass

    def __init__(self, root_dir, config_dir,
                 config_filename = "project.py"):
        self.root_dir = root_dir
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, config_filename)
        self.__config_file_template = templates.project()
        assert os.path.exists(self.__config_file_template)
        self.__configure_function = None
        self.__env = None
        if not os.path.exists(self.config_file):
            self.__bootstrap()
            raise self.NeedUserEdit()
        else:
            self.__read_conf()

    @property
    def env(self):
        return self.__env

    def configure(self, build):
        if self.__configure_function is None:
            raise Exception(
                "The project file %s did not define any `configure` function"
            )
        self.__configure_function(self, build)

    def __bootstrap(self):
        assert self.__env is None
        self.__env = self.__default_env()
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        with open(self.__config_file_template) as template:
            with open(self.config_file, 'w') as conf:
                data = template.read()
                conf.write(data % self.env)

    def __default_env(self):
        env = {}
        env['PROJECT_NAME'] = os.path.basename(os.path.abspath(self.root_dir))
        env['PROJECT_VERSION_NAME'] = 'alpha'
        return Env(self, env)

    def __read_conf(self):
        self.__env = Env(self)
        backup = sys.path[:]
        try:
            sys.path.insert(0, self.config_dir)
            globals_ = {}

            with open(self.config_file) as f:
                exec(f.read(), globals_)

            for k, v in globals_.items():
                if Env.var_re.match(k):
                    self.env[k] = v
                elif k == 'configure':
                    self.__configure_function = v
        finally:
            sys.path = backup

