# -*- encoding: utf-8 -*-

import os
import re

class Value:
    def __init__(self, value, type):
        if type is list and isinstance(value, str):
            value = [value]
        if not isinstance(value, type):
            value = type(value)
        self.value = value
        self.type = type

    def __str__(self):
        return str(self.value)

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

    @property
    def build_vars(self):
        return self.__build_vars

    @property
    def project_vars(self):
        return self.__project_vars

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

    def __getitem__(self, key, type=str):
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
        if not isinstance(var, Value):
            var = Value(var, type)
            self.__dict[key] = var
        return var.value

    def project_set(self, key, value):
        value = Value(value, type(value))
        self.__project_vars[key] = value

    def build_set(self, key, value):
        value = Value(value, type(value))
        self.__build_vars[key] = value

    def get(self, key, default=None, type=None):
        try:
            return self.__getitem__(
                key,
                type=(type is not None and type or str)
            )
        except self.VariableNotFound:
            if default is None and type is not None:
                return type()
            return default

    def __setitem__(self, key, value):
        self.__dict[key] = value

    def __getattr__(self, key):
        return self.__getitem__(key)


    def __iter__(self):
        for item in self.__dict.items():
            yield item

