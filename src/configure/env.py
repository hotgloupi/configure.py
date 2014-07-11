# -*- encoding: utf-8 -*-

from . import tools

import copy
import os
import pickle
import re

#class Value:
#    def __init__(self, value, type_):
#        if type_ is list and isinstance(value, str):
#            raise TypeError("Cannot cast a string to a list")
#        if type_ is bool and isinstance(value, str):
#            bool_values = {
#                '0': False, 'false': False, 'no': False,
#                '1': True, 'true': True, 'yes': True,
#            }
#            value = bool_values.get(value)
#            if value is None:
#                raise Exception("A boolean value must be one of %s" % ', '.join(bool_values.keys()))
#        if not isinstance(value, type_):
#            raise TypeError("%s is not an instance of %s" % (value, type_))
#        self.value = value
#        self.type = type_
#
#    def __str__(self):
#        return str(self.value)

class VariableNotFound(KeyError):
    """Exception raised when accessing a non-existant env variable.
    """
    @property
    def name(self):
        return self.args[0]

class Env:
    """Store/Load variables."""

    var_re = re.compile('^[A-Z][A-Z0-9_]*$')
    valid_types = (str, bool, int, list)

    def __init__(self, vars = {}, parent = None):
        """Create an environment instance. if parent is set, it will be used
        as a fallback when a variable is not found.
        """
        object.__setattr__(self, '_Env__vars', {})
        object.__setattr__(self, '_Env__parent', parent)
        assert self.__parent is None or isinstance(self.__parent, Env)
        self.update(vars)

    #def _enable_vars(self, kind, path, new_vars):
    #    if not os.path.exists(path):
    #        self.__vars[kind] = {}
    #    else:
    #        try:
    #            import pickle
    #            with open(path, 'rb') as f:
    #                self.__vars[kind] = pickle.load(f)
    #                for k, v in self.__vars[kind].items():
    #                    tools.verbose("Load %s=%s from %s cache" % (k, v, kind))
    #            if not isinstance(self.__vars[kind], dict):
    #                raise ValueError("Not a valid cache file !")
    #        except Exception as err:
    #            raise Exception("Couldn't load build vars file '%s'" % path, err)
    #    for k, v in new_vars.items():
    #        self._update_var(kind, k.upper(), v)

    #def _update_var(self, kind, key, val):
    #    d = self.__vars[kind]
    #    value, operator = val['value'], val['op']
    #    if key not in d:
    #        if operator == ':=' and value:
    #            value = [value]
    #        operator = '='

    #    if operator == '=':
    #        if value == '':
    #            if key in d:
    #                tools.verbose("Remove variable", key)
    #                d.pop(key)
    #        else:
    #            tools.verbose("Set variable %s=%s" % (key, value))
    #            d[key] = Value(value, type(value))
    #    elif operator == '+=': # and d[key] exists
    #        if d[key].type != type(value):
    #            raise ValueError(
    #                "Cannot add %s (of type %s) to %s (of type %s)" % (
    #                    value, type(value), d[key].value, d[key].type
    #                )
    #            )
    #        d[key].value += value
    #    elif operator == ':=': # and d[key] exists
    #        if type(value) != str:
    #            raise ValueError(
    #                "Cannot append the value %s of type %s (should be a string)" % (
    #                    value, type(value)
    #                )
    #            )
    #        if d[key].type != list:
    #            raise ValueError(
    #                "Cannot append %s: the variable %s is not a list" % (
    #                    value, key
    #                )
    #            )
    #        d[key].value.append(value)


    def save(self, path):
        """Save this env to the given path."""
        tools.debug("Saving env to", path)
        for k, v in self.__vars.items():
            tools.debug('\t', k, '=', v)
        with open(path, 'wb') as f:
            pickle.dump(self.__vars, f)

    @classmethod
    def load(cls, path, **kw):
        """Create an Env instance from a file. All remaining arguments are
        forwarded to the constructor, except `vars`, which is used to update
        the loaded environment.
        """
        with open(path, 'rb') as f:
            vars = pickle.load(f)
        tools.debug("Loading env from", path)
        for k, v in vars.items():
            tools.debug('\t', k, '=', v)
        vars.update(kw.pop('vars', {}))
        return cls(vars = vars, **kw)

    def update(self, vars):
        """Add or override variables."""
        self.__vars.update(
            dict((k.upper(), copy.deepcopy(v)) for k, v in vars.items())
        )

    def __execute_command(self, cmd):
        return None

    def __getitem__(self, key):
        key = key.upper()
        var = self.__vars.get(key)

        if var is None:
            if self.__parent is not None:
                return self.__parent.__getitem__(key)
            raise VariableNotFound(key)

        return var

    def get(self, key, default = None):
        try:
            return self.__getitem__(key)
        except VariableNotFound:
            return default

    def __setitem__(self, key, value):
        assert type(value) in self.valid_types
        self.__vars[key.upper()] = value
        return value

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    def __iter__(self):
        for item in self.__dict.items():
            yield item

    def keys(self):
        return self.__vars.keys()

    def items(self):
        return self.__vars.items()


from unittest import TestCase

class _(TestCase):

    def test_init(self):
        e = Env()

    def test_init_from_vars(self):
        e = Env({'a': 12})
        self.assertEqual(e['a'], 12)

    def test_ignore_case(self):
        e = Env({'a': 42})
        self.assertEqual(e['a'], 42)
        self.assertEqual(e['A'], 42)

    def test_setitem(self):
        e = Env({'a': 42})
        self.assertEqual(e['A'], 42)
        self.assertEqual(e['a'], 42)
        e['a'] = 24
        self.assertEqual(e['A'], 24)
        self.assertEqual(e['a'], 24)
        e['A'] = 23
        self.assertEqual(e['A'], 23)
        self.assertEqual(e['a'], 23)

    def test_getattr(self):
        e = Env({'a': 42})
        self.assertEqual(e.a, 42)
        self.assertEqual(e.A, 42)


    def test_variable_not_found(self):
        env = Env()
        try:
            res = env['a']
        except VariableNotFound as e:
            self.assertEqual(e.name, 'A')
        else:
            self.fail("Should have raised an error")

        try:
            res = env['A']
        except VariableNotFound as e:
            self.assertEqual(e.name, 'A')
        else:
            self.fail("Should have raised an error")

        try:
            res = env.a
        except VariableNotFound as e:
            self.assertEqual(e.name, 'A')
        else:
            self.fail("Should have raised an error")

        try:
            res = env.A
        except VariableNotFound as e:
            self.assertEqual(e.name, 'A')
        else:
            self.fail("Should have raised an error")

    def test_parent(self):
        p = Env({'a': 32, 'b': 12})
        e = Env({'b': 42, 'c':100}, parent = p)
        self.assertEqual(e.a, 32)
        self.assertEqual(e.b, 42)
        self.assertEqual(e.c, 100)
        self.assertEqual(p.a, 32)
        self.assertEqual(p.b, 12)

    def test_update(self):
        e = Env({'a': 12, 'b': 42})
        e.update({'b': 52, 'c': 62})
        self.assertEqual(e.a, 12)
        self.assertEqual(e.b, 52)
        self.assertEqual(e.c, 62)
