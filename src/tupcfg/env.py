# -*- encoding: utf-8 -*-

from . import tools

import os
import re

class Value:
    def __init__(self, value, type_):
        if type_ is list and isinstance(value, str):
            raise TypeError("Cannot cast a string to a list")
        if type_ is bool and isinstance(value, str):
            bool_values = {
                '0': False, 'false': False, 'no': False,
                '1': True, 'true': True, 'yes': True,
            }
            value = bool_values.get(value)
            if value is None:
                raise Exception("A boolean value must be one of %s" % ', '.join(bool_values.keys()))
        if not isinstance(value, type_):
            raise TypeError("%s is not an instance of %s" % (value, type_))
        self.value = value
        self.type = type_

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
        self.__vars = {
            'build': {},
            'project': {},
        }
        self.project = project

    @property
    def build_vars(self):
        return self.__vars['build']

    @property
    def project_vars(self):
        return self.__vars['project']

    def _enable_vars(self, kind, path, new_vars):
        if not os.path.exists(path):
            self.__vars[kind] = {}
        else:
            try:
                import pickle
                with open(path, 'rb') as f:
                    self.__vars[kind] = pickle.load(f)
                    for k, v in self.__vars[kind].items():
                        tools.verbose("Load %s=%s from %s cache" % (k, v, kind))
                if not isinstance(self.__vars[kind], dict):
                    raise ValueError("Not a valid cache file !")
            except Exception as err:
                raise Exception("Couldn't load build vars file '%s'" % path, err)
        for k, v in new_vars.items():
            self._update_var(kind, k.upper(), v)

    def _update_var(self, kind, key, val):
        d = self.__vars[kind]
        value, operator = val['value'], val['op']
        if key not in d:
            if operator == ':=' and value:
                value = [value]
            operator = '='

        if operator == '=':
            if value == '':
                if key in d:
                    tools.verbose("Remove variable", key)
                    d.pop(key)
            else:
                tools.verbose("Set variable %s=%s" % (key, value))
                d[key] = Value(value, type(value))
        elif operator == '+=': # and d[key] exists
            if d[key].type != type(value):
                raise ValueError(
                    "Cannot add %s (of type %s) to %s (of type %s)" % (
                        value, type(value), d[key].value, d[key].type
                    )
                )
            d[key].value += value
        elif operator == ':=': # and d[key] exists
            if type(value) != str:
                raise ValueError(
                    "Cannot append the value %s of type %s (should be a string)" % (
                        value, type(value)
                    )
                )
            if d[key].type != list:
                raise ValueError(
                    "Cannot append %s: the variable %s is not a list" % (
                        value, key
                    )
                )
            d[key].value.append(value)


    def enable_build_vars(self, path, new_vars={}):
        self._enable_vars('build', path, new_vars)

    def enable_project_vars(self, path, new_vars={}):
        self._enable_vars('project', path, new_vars)

    def _save_vars(self, kind, path):
        try:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(self.__vars[kind], f)
        except Exception as err:
            tools.warning(
                "Couldn't save %s config '%s': %s" % (kind, path, str(err))
            )

    def save_build_vars(self, path):
        self._save_vars('build', path)

    def save_project_vars(self, path):
        self._save_vars('project', path)

    def __execute_command(self, cmd):
        return None

    def __getitem__(self, key, type_=str):
        key = key.upper()
        var = self.__dict.get(
            key,
            os.environ.get(
                key,
                self.__vars['build'].get(
                    key,
                    self.__vars['project'].get(key)
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
            var = Value(var, type(var))
            self.__dict[key] = var
        return var.value

    def project_set(self, key, value):
        key = key.upper()
        tools.verbose("Set %s=%s" % (key, value))
        value = Value(value, type(value))
        self.__vars['project'][key] = value

    def build_set(self, key, value):
        key = key.upper()
        value = Value(value, type(value))
        self.__vars['build'][key] = value

    def get(self, key, default=None, type=None):
        T = type
        key = key.upper()
        try:
            return self.__getitem__(
                key,
                type_=(T is not None and T or str)
            )
        except self.VariableNotFound:
            if default is None and T is not None:
                return T()
            return default

    def __setitem__(self, key, value):
        self.__dict[key] = value

    def __getattr__(self, key):
        return self.__getitem__(key)


    def __iter__(self):
        for item in self.__dict.items():
            yield item

