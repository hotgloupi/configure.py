# -*- encoding: utf-8 -*-

import os
import re

class Env:

    class VariableNotFound(KeyError):
        @property
        def name(self):
            return self.args[0]

    var_re = re.compile('^[A-Z][A-Z0-9_]*$')
    def __init__(self, project, conf={}):
        self.__dict = conf
        self.__project_vars = {}
        self.__build_vars = {}
        self.project = project

    def enable_build_vars(self, path, new_vars={}):
        if not os.path.exists(path):
            self.__build_vars = new_vars
            return
        try:
            import pickle
            with open(path, 'rb') as f:
                self.__build_vars = pickle.load(f)
            if not isinstance(self.__build_vars, dict):
                raise ValueError("Not a valid cache file !")
        except Exception as err:
            raise Exception("Couldn't load build vars file '%s'" % path, err)
        self.__build_vars.update(new_vars)

    def enable_project_vars(self, path, new_vars={}):
        if not os.path.exists(path):
            self.__project_vars = new_vars
            return
        try:
            import pickle
            with open(path, 'rb') as f:
                self.__project_vars = pickle.load(f)
            if not isinstance(self.__project_vars, dict):
                raise ValueError("Not a valid cache file !")
        except Exception as err:
            raise Exception("Couldn't load project vars file '%s'" % path, err)
        self.__project_vars.update(new_vars)

    def save_build_vars(self, path):
        try:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(self.__build_vars, f)
        except Exception as err:
            tools.warning("Couldn't save build config '%s': %s" % (path, str(err)))

    def save_project_vars(self, path):
        try:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(self.__project_vars, f)
        except Exception as err:
            tools.warning("Couldn't save project config '%s': %s" % (path, str(err)))

    def __execute_command(self, cmd):
        return None

    def __getitem__(self, key):
        var = self.__dict.get(
            key,
            os.environ.get(
                key,
                self.__build_vars.get(
                    key,
                    self.__project_vars.get(key)
                )
            )
        )
        if var is None:
            cmd = self.__dict.get(key + '_CMD')
            if cmd is None:
                raise self.VariableNotFound(key)
            var = self.__execute_command(cmd)
            if var is None:
                raise ValueError("Result of command %s_CMD is None" % key)
            self.__dict[key] = var
        return var

    def project_set(self, key, value):
        self.__project_vars[key] = value

    def build_set(self, key, value):
        self.__build_vars[key] = value

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except self.VariableNotFound:
            return default

    def __setitem__(self, key, value):
        self.__dict[key] = value

    def __getattr__(self, key):
        return self.__getitem__(key)


    def __iter__(self):
        for item in self.__dict.items():
            yield item

