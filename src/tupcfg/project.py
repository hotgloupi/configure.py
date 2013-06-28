# -*- encoding: utf-8 -*-

import os
import sys

from . import env
from . import path
from . import tools
from . import templates

from .build import Build

class Project:

    class NeedUserEdit(Exception):
        """Raised if the configuration was generated."""
        pass

    def __init__(self, root_dir, config_dir,
                 config_filename = "project.py",
                 build_vars_filename = ".build_vars",
                 project_vars_filename = ".project_vars",
                 new_project_vars = {}):
        self.root_dir = root_dir #deprecated
        self.directory = path.absolute(root_dir)
        self.config_directory = config_dir
        self.config_file = path.join(config_dir, config_filename)
        self.build_vars_filename = build_vars_filename
        self.project_vars_filename = project_vars_filename

        self.__config_file_template = templates.project()
        assert path.exists(self.__config_file_template)

        self.__configure_function = None
        self.__env = None
        if not path.exists(self.config_file):
            self.__bootstrap()
            raise self.NeedUserEdit()
        else:
            self.__read_conf()
        project_vars_file = path.join(self.config_directory, self.project_vars_filename)
        self.env.enable_project_vars(project_vars_file, new_vars=new_project_vars)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        project_vars_file = path.join(self.config_directory, self.project_vars_filename)
        self.env.save_project_vars(project_vars_file)

    @property
    def env(self):
        return self.__env

    class BuildProxy:
        def __init__(self, project, build_dir, new_build_vars, configure_function, generator_names):
            self.project = project
            self.build_dir = build_dir
            self.configure_function  = configure_function
            self.new_build_vars = new_build_vars
            self.generator_names = generator_names
            self.build = None

        def __enter__(self):
            self.build_vars_file = path.join(
                self.build_dir,
                self.project.build_vars_filename
            )
            self.project.env.enable_build_vars(
                self.build_vars_file,
                new_vars = self.new_build_vars
            )
            self.build = Build(self.project, self.build_dir, self.generator_names)
            self.configure_function(self.project, self.build)
            return self.build

        def __exit__(self, type_, value, traceback):
            self.project.env.save_build_vars(self.build_vars_file)
            self.build.cleanup()

    def configure(self, build_dir, new_build_vars, generator_names):
        if self.__configure_function is None:
            raise Exception(
                "The project file %s did not define any `configure` function"
            )
        return self.BuildProxy(
            self,
            build_dir,
            new_build_vars,
            self.__configure_function,
            generator_names,
        )

    def __bootstrap(self):
        assert self.__env is None
        self.__env = self.__default_env()
        if not path.exists(self.config_directory):
            os.makedirs(self.config_directory)
        with open(self.__config_file_template) as template:
            data = template.read() % self.env
        with open(self.config_file, 'w') as conf:
            conf.write(data)

    def __default_env(self):
        return env.Env(self)

    def __read_conf(self):
        self.__env = env.Env(self)
        backup = sys.path[:]
        try:
            sys.path.insert(0, self.config_directory)
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

