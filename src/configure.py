#! /usr/bin/env python3

import argparse
import os, sys

ROOT_DIR = os.path.dirname(__file__)
PROJECT_CONF_DIR_NAME = ".config"
PROJECT_CONF_DIR = os.path.join(ROOT_DIR, PROJECT_CONF_DIR_NAME).replace('\\', '/')
PROJECT_CONF_TEMPLATES_DIR = os.path.join(PROJECT_CONF_DIR, 'templates').replace('\\', '/')
PROJECT_CONF_FILE = os.path.join(PROJECT_CONF_DIR, "project.py").replace('\\', '/')
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
##      >>> VERSION_NAME_CMD = myPythonFunction
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

# Tup template (used when TUP_TEMPLATE_PATH is None)
# Can be a python function or a shell command that accept a
# relative directory path as only argument and returns (or print out)
# the tup file template.
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
    '.',                            # project root dir
]

# Source directories are treated as tree. If you set this to False, you'll have
# to declare every directory, not just root.
RECURSE_OVER_SOURCE_DIRECTORIES = True

#
# Targets is a list that contains high level targets description. Each target
# is described through a dictionary that contains at least three keys:
#   - 'input_files' (required): Contains a list input files. (can contains
#                               wildcard, see tup manual).
#   - 'command' (required) : The command line to be inserted in the tup rule.
#   - 'output_file' (required): out file name.
#   - 'additional_output_files (optional): a list of additional generated files.
#   - 'output_directory' (optional): where to build out files (defaults to build dir).
#
TARGETS = [
    {
        'input_files': ['*.o'],
        'output_file': my_program
        'output_directory': 'release/bin'
    },
]

###############################################################################
## This section provides examples on how extending project variables (delete or
## comment what's not needed).
##

CC = "gcc"
CXX = "g++"

import sysconfig

PYTHON_DIR          = sysconfig.get_config_var('prefix')
PYTHON_INCLUDE_DIR  = PYTHON_DIR + "/include"
PYTHON_LIBRARY_DIR  = PYTHON_DIR + "/libs"
"""

PROJECT_CONF_TUP_FILE = os.path.join(
    PROJECT_CONF_TEMPLATES_DIR,
    'Tupfile.templates'
).replace('\\', '/')
PROJECT_CONF_TUP_FILE_TEMPLATE = """
include_rules

"""

PROJECT_CONF_TUPRULES_FILE = os.path.join(
    PROJECT_CONF_TEMPLATES_DIR,
    'Tuprules.tup.template'
).replace('\\', '/')
PROJECT_CONF_TUPRULES_FILE_TEMPLATE = """
# This file is generated in each build directory.
# All project variables and the following ones are defined:
#   * BUILD_TYPE
#

BUILD_TYPE = %(BUILD_TYPE)s
BUILD_DIR = $(TUP_CWD)
SOURCE_DIR = $(BUILD_DIR)/..

CC = %(CC)s
CXX = %(CXX)s

CFLAGS      +=  -I%(PYTHON_INCLUDE_DIR)s
CXXFLAGS    +=  -std=c++0x
!make_cpp_object = |> $(CXX) $(CCFLAGS) $(CXXFLAGS) $(CXXFLAGS_%%f) -c %%f -o %%o |> %%b.o

"""

def detectDefaults():
    defaults = {}
    defaults['project_conf_dir_name'] = PROJECT_CONF_DIR_NAME
    defaults['project_name'] = os.path.basename(os.path.abspath(ROOT_DIR)).replace('\\', '/')
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
    def __init__(self, module):
        self._module = module

    @staticmethod
    def _executeCommand(cmd):
        return None

    def __getattr__(self, key):
        var = getattr(self._module, key)
        if var is None:
            cmd = getattr(self._module, key + '_CMD')
            if cmd is None:
                raise KeyError("both %s and %s_CMD are None" % (key, key))
            var = self._executeCommand(cmd)
            if var is None:
                raise ValueError("Result of command %s_CMD is None" % key)
        if isinstance(var, str):
            return var.replace('\\', '/')
        return var

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __iter__(self):
        for k in dir(self._module):
            if k.startswith('__') or k.endswith('_CMD'):
                continue
            try:
                v = self.__getattr__(k)
            except:
                continue
            yield (k, v)


def getConf(module_name):
    backup = sys.path[:]
    try:
        sys.path.insert(0, PROJECT_CONF_DIR)
        imported_module = __import__(module_name)
    finally:
        sys.path = backup

    return ConfProxy(imported_module)


def parseArguments(project):
    parser = argparse.ArgumentParser(
        description="Configure '%s' project" % project.NAME
    )
    parser.add_argument('--build-type',
                        default=project.DEFAULT_BUILD_TYPE,
                        help="Enable a build type")
    parser.add_argument('build_dir', action="store",
                        help="Where to build your project")
    #parser.add_argument('--release', action='store_true')
    #parser.add_argument('--version-major', type=int, default=VERSION_MAJOR)
    #parser.add_argument('--version-name', default=VERSION_NAME)
    #parser.add_argument('--version-minor', type=int, default=VERSION_MINOR)
    #parser.add_argument('--version-hash', default=VERSION_HASH)
    #parser.add_argument('--tup-bin', default=which('tup'))
    #parser.add_argument('--dc-bin', default=(which('dmd') or which('gdc') or which('ldc')))
    return parser.parse_args()

class BuildEnv:
    def __init__(self, project, args):
        self._project = project
        self._build_type = args.build_type.lower()
        self._build_dir = args.build_dir

    def _setupDir(self):
        if not os.path.exists(self._build_dir):
            os.mkdir(self._build_dir)

    @property
    def project_dict(self):
        p = {}
        p.update(self._project)
        p['BUILD_TYPE'] = self._build_type
        return p

    def _setupTuprules(self):
        with open(self._project.TUPRULES_TEMPLATE_PATH, 'r') as f:
            template = f.read()
        with open(os.path.join(self._build_dir, 'Tuprules.tup'), 'w') as f:
            f.write(template % self.project_dict)

    def setup(self):
        self._setupDir()
        self._setupTuprules()

def main():
    if needBootstrap():
        return bootstrap()
    assert os.path.isdir(PROJECT_CONF_DIR)
    project = getConf('project')
    args = parseArguments(project)
    print("-- Configure '%s' project" % project.NAME)
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
