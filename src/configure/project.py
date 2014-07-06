# -*- encoding: utf-8 -*-

import os
import sys

from .env import Env
from . import path
from . import tools
from . import templates

from .build import Build

class Project:

    @classmethod
    def initialize(self, config_directory, config_filename):
        """Prepare a project skeleton."""
        config_file = path.join(config_directory, config_filename)
        if path.exists(config_file):
            tools.fatal(
                "This project seems to be already initialized, see '%s'" % path.clean(config_file, replace_home = True)
            )
        if not path.exists(config_directory):
            os.makedirs(config_directory)
        with open(templates.project()) as template:
            data = template.read()
        with open(config_file, 'w') as conf:
            conf.write(data)

    def __init__(self, directory, config_dir,
                 config_filename = "project.py",
                 build_env_filename = ".build-env",
                 project_env_filename = ".project-env",
                 new_project_env = {}):
        self.directory = path.absolute(directory)
        self.config_directory = config_dir
        self.config_file = path.join(config_dir, config_filename)
        self.build_env_filename = build_env_filename
        self.project_env_filename = project_env_filename

        self.__configure_function = None
        self.__env = None
        if not path.exists(self.config_file):
            raise Exception("This directory '%s' does not seem to contains a configuration")
        self.__read_conf()
        self.project_env_file = path.join(self.config_directory, self.project_env_filename)
        self.env.update(new_project_env)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.env.save(self.project_env_file)

    @property
    def env(self):
        return self.__env

    class BuildProxy:
        def __init__(self,
                     project,
                     build_dir,
                     new_build_env,
                     configure_function,
                     generator_names):
            self.project = project
            self.build_dir = build_dir
            self.configure_function  = configure_function
            self.new_build_env = new_build_env
            self.generator_names = generator_names
            self.build = None
            self.build_env_file = path.join(
                self.build_dir,
                self.project.build_env_filename
            )

        def __enter__(self):
            kw = {'parent': self.project.env,
                  'vars': self.new_build_env}
            if os.path.exists(self.build_env_file):
                env = Env.load(self.build_env_file, **kw)
            else:
                env = Env(**kw)
            env.update(self.new_build_env)
            self.build = Build(
                self.project,
                self.build_dir,
                self.generator_names,
                env = env
            )
            self.configure_function(self.build)
            return self.build

        def __exit__(self, type_, value, traceback):
            self.build.env.save(self.build_env_file)
            self.build.cleanup()

    def configure(self, build_dir, new_build_vars, generator_names):
        if self.__configure_function is None:
            raise Exception(
                "The project file %s did not define any `main` function"
            )
        return self.BuildProxy(
            self,
            build_dir,
            new_build_vars,
            self.__configure_function,
            generator_names,
        )

    def __read_conf(self):
        self.__env = Env()
        backup = sys.path[:]
        try:
            sys.path.insert(0, self.config_directory)
            globals_ = {}

            with open(self.config_file) as f:
                exec(f.read(), globals_)

            for k, v in globals_.items():
                if Env.var_re.match(k):
                    self.env[k] = v
                elif k == 'main':
                    self.__configure_function = v
        finally:
            sys.path = backup

