#! /usr/bin/env python3

import argparse
import os, sys

def cleanpath(p):
    p = os.path.normpath(p).replace('\\', '/')
    if p.startswith('./'):
        return p[2:]
    return p

def cleanjoin(*args):
    return cleanpath(os.path.join(*args))

ROOT_DIR = cleanpath(os.path.dirname(__file__))
PROJECT_CONF_DIR_NAME = ".config"
PROJECT_CONF_DIR = cleanjoin(ROOT_DIR, PROJECT_CONF_DIR_NAME)
PROJECT_CONF_TEMPLATES_DIR = cleanjoin(PROJECT_CONF_DIR, 'templates')
PROJECT_CONF_FILE = cleanjoin(PROJECT_CONF_DIR, "project.py")
PROJECT_CONF_FILE_TEMPLATE = """# -*- encoding: utf-8 -*-

# The project name (this is not the version code name).
NAME = %(project_name)s

##
## Note: Every variable can be computed with a command or a function each time
## the configure script is ran. To do so, just set the variable to `None', and
## set another variable named exactly as the first one, but suffixed with '_CMD'.
## For example,
##      >>> VERSION_NAME = None                                 # necessary
##      >>> VERSION_NAME_CMD = "git --describe"                 # retreive with git
##      >>> VERSION_NAME_CMD = ["git", "--describe"]            # safer syntax
##      >>> def myPythonFunction() : return 32                  # simple function
##      ...
##      >>> VERSION_NAME_CMD = _myPythonFunction
##

# The version name (could be "alpha" for example)
VERSION_NAME = %(project_version_name)s
VERSION_NAME_CMD = %(project_version_name_cmd)s

# Availables build types (see build/ files)
BUILD_TYPES = ['Debug', 'Release']
DEFAULT_BUILD_TYPE = 'Debug'

# Tup template file path
TUP_TEMPLATE_PATH = %(project_conf_tup_file)s
TUP_TEMPLATE_PATH_CMD = None

# Tup template generator (used when TUP_TEMPLATE_PATH is None).
# Can be a python function or a shell command that accept a relative directory
# path as only argument and respectively returns or print out the tup file
# template.
TUP_TEMPLATE_GEN = None
TUP_TEMPLATE_GEN_CMD = None

# tup build specific rules template file path
TUPRULES_TEMPLATE_PATH = %(project_conf_tuprules_file)s
TUPRULES_TEMPLATE_PATH_CMD = None

#
# Define here where source files can be found. The default behavior is to
# recurse over source directories. Set RECURSE_OVER_SOURCE_DIRECTORIES to False
# to change that.
#
SOURCE_DIRECTORIES = [
    'src',                            # project root dir
]

# Source directories are treated as tree. If you set this to False, you'll have
# to declare every directory, not just root.
RECURSE_OVER_SOURCE_DIRECTORIES = True

###############################################################################
# Targets is a list that contains high level targets description. Each target
# is described through a dictionary that contains the following keys:
#   - 'input_items' (required): Contains a list input items (see below).
#   - 'additional_inputs' (optional): Contains a list of additional input items
#   - 'command' (required) : The command line to be inserted in the tup rule.
#   - 'output_file' (required): out file name.
#   - 'additional_output_files (optional): a list of additional generated files.
#   - 'output_directory' (optional): where to build out files (defaults to build dir).
#

import sys as _sys

# Convenient function to get a portable executable name
def executable(name):
    return name + (_sys.platform.startswith('win') and '.exe' or '')

TARGETS = [
    {
        'input_items': [('src', '*.o')],
        'command': 'link_cpp_executable',
        'output_file': executable('my_program'),
        'output_directory': 'release/bin',
    },
]

# Same as before
RECURSE_OVER_TARGET_DIRECTORIES = True

###############################################################################
## This section provides examples on how extending project variables (delete or
## comment what's not needed).
##

CC = "gcc"
CXX = "g++"

import sysconfig as _sysconfig

PYTHON_DIR          = _sysconfig.get_config_var('prefix')
PYTHON_INCLUDE_DIR  = PYTHON_DIR + "/include"
PYTHON_LIBRARY_DIR  = PYTHON_DIR + "/libs"
PYTHON_LIBRARY      = 'python32'

BOOST_INCLUDE_DIR           = None
BOOST_LIBRARY_DIR           = None

BOOST_PYTHON_LIBRARY        = None

"""

PROJECT_CONF_TUP_FILE = cleanjoin(
    PROJECT_CONF_TEMPLATES_DIR,
    'Tupfile.templates'
)
PROJECT_CONF_TUP_FILE_TEMPLATE = """
include_rules

: foreach {SOURCE_DIR}/*.cpp |> !make_cpp_object |>

"""

PROJECT_CONF_TUPRULES_FILE = cleanjoin(
    PROJECT_CONF_TEMPLATES_DIR,
    'Tuprules.tup.template'
)
PROJECT_CONF_TUPRULES_FILE_TEMPLATE = """
# This file is generated in each build directory.
# All project variables and the following ones are defined:
#   * BUILD_TYPE
#

BUILD_TYPE = {BUILD_TYPE}
BUILD_DIR = $(TUP_CWD)
SOURCE_DIR = $(BUILD_DIR)/..

CC = {CC}
CXX = {CXX}

CFLAGS      +=  -I{PYTHON_INCLUDE_DIR} -I{BOOST_INCLUDE_DIR}
CXXFLAGS    +=  -std=c++0x
LDFLAGS     +=  -L{PYTHON_LIBRARY_DIR} -Wl,-static -l{PYTHON_LIBRARY} \\
                -L{BOOST_LIBRARY_DIR}  -Wl,-static -l{BOOST_PYTHON_LIBRARY} \\

!make_cpp_object = |> $(CXX) $(CFLAGS) $(CXXFLAGS) $(CXXFLAGS_%f) -c %f -o %o |> %b.o
!link_cpp_executable = |> $(CXX) $(LDFLAGS) %f $(LDFLAGS) $(LDFLAGS_%f) -o %o |>

"""


def detectDefaults():
    defaults = {}
    defaults['project_conf_dir_name'] = PROJECT_CONF_DIR_NAME
    defaults['project_name'] = os.path.basename(os.path.abspath(ROOT_DIR))
    defaults['project_version_name'] = 'alpha'
    defaults['project_version_name_cmd'] = None
    defaults['project_conf_tup_file'] = PROJECT_CONF_TUP_FILE
    defaults['project_conf_tuprules_file'] = PROJECT_CONF_TUPRULES_FILE

    return defaults

def needBootstrap():
    return not os.path.exists(PROJECT_CONF_FILE)

def bootstrap():
    defaults = detectDefaults()
    if not os.path.exists(PROJECT_CONF_DIR):
        os.makedirs(PROJECT_CONF_DIR)
    with open(PROJECT_CONF_FILE, 'w') as f:
        f.write(PROJECT_CONF_FILE_TEMPLATE % dict(
            (k, repr(v)) for k, v in defaults.items()
        ))
    if not os.path.exists(PROJECT_CONF_TEMPLATES_DIR):
        os.makedirs(PROJECT_CONF_TEMPLATES_DIR)
    with open(PROJECT_CONF_TUP_FILE, 'w') as f:
        f.write(PROJECT_CONF_TUP_FILE_TEMPLATE)
    with open(PROJECT_CONF_TUPRULES_FILE, 'w') as f:
        f.write(PROJECT_CONF_TUPRULES_FILE_TEMPLATE)
    print("Please edit %s and re-run the configure script" % PROJECT_CONF_FILE)

class ConfProxy:
    def __init__(self, module, globals_):
        self._module = module
        self._dict = {}
        for k, v in globals_.items():
            if getattr(self._module, k) is None:
                self._dict[k] = v

    @staticmethod
    def _executeCommand(cmd):
        return None

    def __getattr__(self, key):
        var = self._dict.get(key)
        if var is None:
            var = getattr(self._module, key)
            if var is None:
                cmd = getattr(self._module, key + '_CMD')
                if cmd is None:
                    raise KeyError("both %s and %s_CMD are None" % (key, key))
                var = self._executeCommand(cmd)
                if var is None:
                    raise ValueError("Result of command %s_CMD is None" % key)
            if isinstance(var, str):
                var = cleanpath(var)
            self._dict[key] = var
        return var

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __iter__(self):
        for k in dir(self._module):
            if k.startswith('_') or k.endswith('_CMD'):
                continue
            try:
                v = self.__getattr__(k)
            except:
                continue
            yield (k, v)



class BuildEnv:

    _required_target_keys = [
        'input_items', 'command', 'output_file'
    ]

    _available_target_keys = _required_target_keys + [
        'additional_input_files',
        'additional_output_files',
        'output_directory',
    ]

    def __init__(self, project, args):
        self._project = project
        self._build_type = (args.build_type or self._project.DEFAULT_BUILD_TYPE).lower()
        self._build_dir = cleanjoin(ROOT_DIR, args.build_dir)

    def _setupDir(self):
        if not os.path.exists(self._build_dir):
            os.mkdir(self._build_dir)

    def _getProjectDict(self, **kwargs):
        kwargs.update(self._project)
        return kwargs

    def _setupTuprules(self):
        with open(self._project.TUPRULES_TEMPLATE_PATH, 'r') as f:
            template = f.read()
        project_dict = self._getProjectDict(
            BUILD_TYPE=self._build_type
        )
        with open(os.path.join(self._build_dir, 'Tuprules.tup'), 'w') as f:
            f.write(template.format(**project_dict))

    def _setupTupfile(self, source_dir, build_dir):
        tup_file = os.path.join(build_dir, 'Tupfile')
        print(
            '--',
            os.path.exists(tup_file) and "Updating" or "Creating",
            "'%s'." % cleanpath(tup_file)
        )
        template_path = self._project.TUP_TEMPLATE_PATH
        with open(template_path, 'r') as f:
            template = f.read()
        project_dict = self._getProjectDict(
            SOURCE_DIR=cleanpath(os.path.relpath(source_dir, start=build_dir)),
        )
        with open(tup_file, 'w') as f:
            f.write(template.format(**project_dict))

    def _setupSourceDirectory(self, rel_source_dir):
        source_dir = cleanjoin(ROOT_DIR, rel_source_dir)
        if not os.path.exists(source_dir):
            raise Exception("The folder '%s' does not exists" % source_dir)
        assert os.path.isdir(source_dir)
        if os.path.samefile(source_dir, ROOT_DIR):
            raise Exception(
                "The root directory '%s' cannot be a source directory" % os.path.abspath(ROOT_DIR)
            )

        for root, dirnames, filenames in os.walk(source_dir):
            build_dir = os.path.join(self._build_dir, rel_source_dir)
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            self._setupTupfile(source_dir, build_dir)

    def _parseTargetInputs(self, inputs, output_directory):
        for input_ in inputs:
            if isinstance(input_, str):
                print("str:", input_)
                yield cleanpath(os.path.relpath(
                    os.path.join(self._build_dir, input_),
                    start=output_directory
                ))
            elif isinstance(input_, tuple):
                assert len(input_) == 2
                build_dir, file_ = (cleanjoin(self._build_dir, input_[0]), cleanpath(input_[1]))
                assert '/' not in file_
                for root, dirnames, filenames in os.walk(build_dir):
                    yield '%s/%s' % (
                        cleanpath(os.path.relpath(root, start=output_directory)),
                        file_
                    )
                    if not self._project.RECURSE_OVER_TARGET_DIRECTORIES:
                        break
            else:
                raise ValueError("Unknown item type : %s" % str(input_))

    def _parseTarget(self,
                     input_items=None,
                     additional_input_files=None,
                     command=None,
                     output_file=None,
                     additional_output_files=None,
                     output_directory=None):
        output_directory = cleanjoin(self._build_dir, output_directory or '.')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # backslash + linefeed padded
        bslf = lambda s: '%s\\\n' % (len(s) < 79 and (s + (79 - len(s)) * ' ') or s)

        result = ':\\\n'
        for input_ in  self._parseTargetInputs(input_items, output_directory):
            result += bslf('  %s' % input_)

        if additional_input_files is not None:
            raise NotImplemented()

        result += bslf('    |> !%s' % command)

        result += bslf('    |> %s' % output_file)

        if additional_output_files is not None:
            raise NotImplemented()

        result += '\n'
        return (output_directory, result)

    def setup(self):
        self._setupDir()
        self._setupTuprules()
        for source_dir in self._project.SOURCE_DIRECTORIES:
            self._setupSourceDirectory(source_dir)
        target_dirs = {}
        for target in self._project.TARGETS:
            for k in self._required_target_keys:
                if not k in target:
                    raise KeyError("Missing key '%s' for target %s" % (k, str(target)))
            for k in target.keys():
                if not k in self._available_target_keys:
                    raise KeyError("Invalid key '%s' for target %s" % (k, str(target)))
            dir_, res = self._parseTarget(**target)
            target_dirs.setdefault(dir_, []).append(res)
        for target_dir, rules in target_dirs.items():
            content = 'include_rules\n\n' + ('\n' + '#' * 80 + '\n').join(rules)
            tup_file = cleanjoin(target_dir, 'Tupfile')
            print(
                '--',
                os.path.exists(tup_file) and 'Updating' or 'Creating',
                "'%s'." % tup_file
            )
            with open(tup_file, 'w') as f:
                f.write(content)


def getConf(module_name, globals={}):
    backup = sys.path[:]
    try:
        import importlib
        sys.path.insert(0, PROJECT_CONF_DIR)
        imported_module = importlib.__import__(module_name, globals=globals)
    finally:
        sys.path = backup

    return ConfProxy(imported_module, globals)


def parseArguments():
    parser = argparse.ArgumentParser(
        description="Configure your project"
    )
    parser.add_argument('build_dir', action="store",
                        help="Where to build your project")
    parser.add_argument('--build-type', default=None,
                        help="Enable a build type")
    parser.add_argument('-D', '--define', action='append',
                        help="Define build specific variables")
    #parser.add_argument('--release', action='store_true')
    #parser.add_argument('--version-major', type=int, default=VERSION_MAJOR)
    #parser.add_argument('--version-name', default=VERSION_NAME)
    #parser.add_argument('--version-minor', type=int, default=VERSION_MINOR)
    #parser.add_argument('--version-hash', default=VERSION_HASH)
    #parser.add_argument('--tup-bin', default=which('tup'))
    #parser.add_argument('--dc-bin', default=(which('dmd') or which('gdc') or which('ldc')))
    return parser.parse_args()

def main():
    if needBootstrap():
        return bootstrap()
    assert os.path.isdir(PROJECT_CONF_DIR)
    args = parseArguments()

    globals_ = {}
    for define in args.define:
        s = define.split('=')
        if len(s) != 2:
            raise Exception("Wrong define '%s', should be in the NAME=VALUE form")
        k, v = s[0].strip(), cleanpath(s[1])
        globals_[k] = v
    project = getConf('project', globals_)
    print("-- Configure '%s' project." % project.NAME)
    build_env = BuildEnv(project, args)

    build_env.setup()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Unexpected error: ", str(e), file=sys.stderr)
        from traceback import format_tb
        for tb in format_tb(e.__traceback__):
            print("===============================")
            print(tb)
