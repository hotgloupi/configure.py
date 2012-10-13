# -*- encoding: utf-8 -*-

import os
import sys

from . import env
from . import tools
from . import templates

class Project:

    class NeedUserEdit(Exception):
        """Raised if the configuration was generated."""
        pass

    def __init__(self, root_dir, config_dir,
                 config_filename = "project.py",
                 build_vars_filename = ".build_vars",
                 project_vars_filename = ".project_vars"):
        from os.path import join, exists
        self.root_dir = root_dir
        self.config_dir = config_dir
        self.config_file = join(config_dir, config_filename)
        self.build_vars_filename = build_vars_filename
        self.project_vars_filename = project_vars_filename

        self.__config_file_template = templates.project()
        assert exists(self.__config_file_template)

        self.__configure_function = None
        self.__env = None
        if not exists(self.config_file):
            self.__bootstrap()
            raise self.NeedUserEdit()
        else:
            self.__read_conf()

    @property
    def env(self):
        return self.__env

    def configure(self, build, new_build_vars={}, new_project_vars={}):
        if self.__configure_function is None:
            raise Exception(
                "The project file %s did not define any `configure` function"
            )
        build_vars_file = os.path.join(build.directory, self.build_vars_filename)
        project_vars_file = os.path.join(self.config_dir, self.project_vars_filename)

        self.env.enable_build_vars(build_vars_file, new_vars=new_build_vars)
        self.env.enable_project_vars(project_vars_file, new_vars=new_project_vars)
        self.__configure_function(self, build)
        self.env.save_build_vars(build_vars_file)
        self.env.save_project_vars(project_vars_file)

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
        return env.Env(self)

    def __read_conf(self):
        self.__env = env.Env(self)
        backup = sys.path[:]
        try:
            sys.path.insert(0, self.config_dir)
            globals_ = {}

            with open(self.config_file) as f:
                exec(f.read(), globals_)

            for k, v in globals_.items():
                if env.Env.var_re.match(k):
                    self.env[k] = v
                elif k == 'configure':
                    self.__configure_function = v
        finally:
            sys.path = backup

