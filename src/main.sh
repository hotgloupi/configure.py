#!/bin/sh
# Python file written with a shell helper (mainly for windows).
__SHELL_PROTECT=""" "
SCRIPT="$0"
PYTHON=`which python3`

if [ -z "$PYTHON" ]
then
	PYTHON=`which python`
fi

if [ -z "$PYTHON" ]
then
	echo "Cannot find python executable"
	exit 1
fi

export CONFIGURE_ROOT_DIR="`dirname $SCRIPT`"

"$PYTHON" "$0" "$@"

exit $?

__SHELL_PROTECT=" """

import sys
try:
    if sys.version_info[0] != 3:
        raise Exception("Invalid python version")
except:
    print("Invalid python version")
    sys.exit(1)

import argparse
import os
import pipes
import re
import shutil
import stat
import subprocess
import sys
import cgitb

def cleanpath(p, **kwargs):
    p = os.path.normpath(p)
    if p.startswith('./'):
        p =  p[2:]
    if kwargs.get('replace_home'):
        p = os.path.join(
            '~',
            os.path.relpath(p, start=os.path.expanduser('~')),
        )
    return p.replace('\\', '/')

def cleanabspath(p, **kwargs):
    return cleanpath(os.path.abspath(p), **kwargs)

def cleanjoin(*args, **kwargs):
    return cleanpath(os.path.join(*args), **kwargs)

FATAL = "[ cfg ] FATAL"
ERROR = "[ cfg ] ERROR"
STATUS = "[ cfg ]"

def err(*args, **kwargs):
    kwargs['file'] = sys.stderr
    return print(*args, **kwargs)

def status(*args, **kwargs):
    return print(STATUS, *args, **kwargs)

def error(*args, **kwargs):
    return err(ERROR, *args, **kwargs)

def fatal(*args, **kwargs):
    try:
        err(FATAL, *args, **kwargs)
    finally:
        sys.exit(1)

def which(binary):
    paths = os.environ['PATH'].split(os.path.pathsep)
    for dir_ in paths:
        path = os.path.join(dir_, binary)
        if os.path.exists(path) and os.stat(path)[stat.ST_MODE] & stat.S_IXUSR:
            return path
    if sys.platform =='win32' and not binary.lower().endswith('.exe'):
        return which(binary + '.exe')
    return None

def cmd(cmd, stdin = b'', cwd = None, env=None):
    sys.stderr.flush()
    p = subprocess.Popen(cmd,
                         cwd = cwd,
                         stdin = subprocess.PIPE,
                         shell = False,
                         env = env)
    p.stdin.write(stdin)
    p.stdin.close()
    p.wait()
    if p.returncode != 0:
        raise Exception("Command failed")

DEBUG = True
VERBOSE = True
ROOT_DIR = None
HOME_URL = "http://hotgloupi.fr/configure.py.html"
TUP_HOME_URL = "http://gittup.org"
PROJECT_CONFIG_DIR_NAME = ".config"
PROJECT_CONFIG_DIR = None
PROJECT_CONFIG_FILENAME = "project.py"
TUP_INSTALL_DIR = None
TUP_GIT_URL = "git://github.com/gittup/tup.git"
TUP_WINDOWS_URL = "http://gittup.org/tup/win32/tup-latest.zip"
CONFIGURE_PY_INSTALL_DIR = None
CONFIGURE_PY_GIT_URL = "git://github.com/hotgloupi/configure.git"
CONFIGURE_PY_GENERATORS = ['Tup', 'Makefile']


def reset_root_dir(root):
    """Compute global variables according to the project root directory"""
    global ROOT_DIR, PROJECT_CONFIG_DIR, TUP_INSTALL_DIR, CONFIGURE_PY_INSTALL_DIR
    ROOT_DIR = cleanpath(root)
    PROJECT_CONFIG_DIR = cleanjoin(ROOT_DIR, PROJECT_CONFIG_DIR_NAME)
    TUP_INSTALL_DIR = cleanjoin(PROJECT_CONFIG_DIR, 'tup')
    CONFIGURE_PY_INSTALL_DIR = cleanjoin(PROJECT_CONFIG_DIR, 'configure.py')
reset_root_dir(
    os.environ.get("CONFIGURE_PY_ROOT_DIR", os.path.dirname(__file__))
)


def self_install(args):
    status("Installing configure.py in", CONFIGURE_PY_INSTALL_DIR)
    if not os.path.exists(CONFIGURE_PY_INSTALL_DIR):
        os.makedirs(CONFIGURE_PY_INSTALL_DIR)
        status("Getting tup from", CONFIGURE_PY_GIT_URL)
        cmd(['git', 'clone', CONFIGURE_PY_GIT_URL, CONFIGURE_PY_INSTALL_DIR])
    else:
        status("Updating configure.py")
        cmd(['git', 'pull'], cwd=CONFIGURE_PY_INSTALL_DIR)

def tup_install(args):
    from configure import platform
    if platform.IS_WINDOWS:
        tup_install_windows(args)
    else:
        tup_install_git(args)
    from configure import tools
    print("Tup installed in", tools.which('tup'))


def tup_install_windows(args):
    import urllib.request as r
    req = r.urlopen(TUP_WINDOWS_URL)
    if not os.path.exists(TUP_INSTALL_DIR):
        os.makedirs(TUP_INSTALL_DIR)
    tarball = os.path.join(TUP_INSTALL_DIR, 'tup.zip')
    with open(tarball, 'wb') as f:
        while True:
            data = req.read(4096)
            if not data:
                break
            f.write(data)
    import zipfile
    with zipfile.ZipFile(tarball) as f:
        f.extractall(TUP_INSTALL_DIR)


def tup_install_git(args):
    from configure import path
    status("Installing tup in", TUP_INSTALL_DIR)
    if not path.exists(TUP_INSTALL_DIR):
        os.makedirs(TUP_INSTALL_DIR)
        status("Getting tup from", TUP_GIT_URL)
        cmd(['git', 'clone', TUP_GIT_URL, TUP_INSTALL_DIR])
    else:
        status("Updating tup")
        cmd(['git', 'pull'], cwd=TUP_INSTALL_DIR)

    tup_shell_bin = path.join(TUP_INSTALL_DIR, "build", "tup")
    if not path.exists(TUP_INSTALL_DIR, "build", "tup"):
        cmd(['sh', 'build.sh'], cwd=TUP_INSTALL_DIR)
    else:
        status("Found shell version of tup at", tup_shell_bin)

    tup_dir = path.join(ROOT_DIR, '.tup')
    if os.path.exists(tup_dir):
        os.rename(tup_dir, tup_dir + '.bak')

    try:
        if not path.exists(TUP_INSTALL_DIR, '.tup'):
            cmd(['./build/tup', 'init'], cwd=TUP_INSTALL_DIR)
        cmd(['./build/tup', 'upd'], cwd=TUP_INSTALL_DIR)
    finally:
        if path.exists(tup_dir + '.bak'):
            os.rename(tup_dir + '.bak', tup_dir)


def prepare_build(args, defines, exports):
    import configure # Should work at this point
    from configure.path import exists, join, absolute

    build_dir = args.build_dir
    try:
        project = configure.Project(
            ROOT_DIR,
            PROJECT_CONFIG_DIR,
            config_filename = PROJECT_CONFIG_FILENAME,
            new_project_vars = exports,
        )

        env_build_dirs = list(
            d for d in project.env.get('BUILD_DIRECTORIES', [])
            if exists(d, '.configure.py_build')
        )
        configure.tools.verbose("Found build directories:", ' '.join(env_build_dirs))
        build_dirs = []
        if build_dir is not None:
            build_dirs = [build_dir]
            tup_build_marker = join(build_dir, '.configure.py_build')
            if not exists(build_dir):
                os.makedirs(build_dir)
                with open(tup_build_marker, 'w') as f:
                    pass
            elif not exists(tup_build_marker):
                fatal('\n'.join([
                    "'%(build_dir)s' doest not seem to be a tup build directory:",
                    "\t* Remove this directory",
                    "\t* Touch the file %(tup_build_marker)s",
                ]) % locals())
        else:
            build_dirs = env_build_dirs

        if not build_dirs:
            fatal("No build directory specified on command line. (try -h switch)")

        project.env.project_set(
            'BUILD_DIRECTORIES',
            list(set(build_dirs + env_build_dirs))
        )

        if args.dump_vars:
            status("Project variables:")
            for k, v in project.env.project_vars.items():
                status("\t - %s = %s" % (k, v))

        with project:
            for build_dir in build_dirs:
                with project.configure(build_dir, defines, args.generator) as build:
                    if args.dump_vars:
                        status("Build variables for directory '%s':" % build_dir)
                        build_vars = project.env.build_vars
                        keys = sorted(build_vars.keys())
                        for k in keys:
                            status("\t - %s = %s" % (k, build_vars[k]))
                        continue

                    if args.dump_build:
                        build.dump()
                    else:
                        build.generate()

    except configure.Project.NeedUserEdit:
        print(
            "Please edit %s and re-run the configure script" % join(
                PROJECT_CONFIG_DIR,
                PROJECT_CONFIG_FILENAME,
                replace_home=True,
            )
        )
        sys.exit(0)


def parse_args():
    def Dir(s):
        if not os.path.isdir(s):
            raise argparse.ArgumentTypeError
        return s
    parser = argparse.ArgumentParser(
        description="Configure your project for tup"
    )
    parser.add_argument('build_dir', action="store",
                        help="Where to build your project", nargs='?')
    parser.add_argument('-D', '--define', action='append',
                        help="Define build specific variables", default=[])
    parser.add_argument('-E', '--export', action='append',
                        help="Define project specific variables", default=[])
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose mode")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('--dump-vars', action='store_true', help="dump variables")
    parser.add_argument('--dump-build', action='store_true', help="dump commands that would be executed")
    parser.add_argument('--install', action='store_true', help="install when needed")
    parser.add_argument('--self-install', action='store_true', help="install (or update) configure.py")
    parser.add_argument('--tup-install', action='store_true', help="install (or update) tup")
    parser.add_argument('--generator', '-G', default = None,
                        help = "Generate build rules for another build system",
                       choices = CONFIGURE_PY_GENERATORS)
    parser.add_argument('--root-dir', help = "Root project directory",
                        action = 'store',
                        default = ROOT_DIR)

    return parser, parser.parse_args()

def parse_cmdline_variables(args):
    res = {}
    for arg in args:
        arg = arg.strip()
        if '=' not in arg:
            fatal("'=' not found in define: use %s=true to define a boolean variable" % arg)
        parts = arg.split('=')
        k = parts[0].strip()
        v = '='.join(parts[1:]).strip()
        op = '='
        for p in ['+', ':']:
            if k.endswith(p):
                op = p + '='
                k = k[:-1]
                break
        if v.lower() in ['1', 'true']:
            v = True
        elif v.lower() in ['0', 'false']:
            v = False
        elif v.startswith('['):
            if not v.endswith(']'):
                fatal("Missing ']' when defining %s" % k)
            v = [e.strip() for e in v[1:-1].split(',')]
        res[k] = {
            'op': op,
            'value': v,
        }
    return res

def main():
    parser, args = parse_args()

    DEBUG = args.debug
    VERBOSE = args.verbose
    reset_root_dir(args.root_dir)

    if DEBUG:
        status("root directory set to", ROOT_DIR)
        cgitb.enable(format = 'text')


    from os.path import exists, join
    sys.path.insert(0, join(PROJECT_CONFIG_DIR,'configure.py/src'))
    sys.path.insert(0, PROJECT_CONFIG_DIR)

    have_configure = False
    try:
        import configure
        have_configure = True
    except ImportError: pass

    if args.self_install or (args.install and not have_configure):
        self_install(args)
        try:
            import imp
            file_, pathname, descr = imp.find_module("configure", [PROJECT_CONFIG_DIR])
            configure = imp.load_module("configure", file_, pathname, descr)
        except Exception as e:
            fatal("Sorry, configure installation failed for some reason:", e)

    try:
        import configure

        # configure.py will use these functions to log
        configure.tools.status = status
        configure.tools.error = error
        configure.tools.fatal = fatal

        configure.tools.DEBUG = DEBUG
        configure.tools.VERBOSE = VERBOSE or DEBUG
    except ImportError as e:
        if DEBUG is True:
            raise e

        fatal(
            '\n'.join([
                "Cannot find configure.py module, your options are:",
                "\t* Just use the --self-install flag (installed in %(config_dir)s/configure.py)",
                "\t* Add it as a submodule: `git submodule add git@github.com:hotgloupi/configure.py.git %(config_dir)s/configure.py`",
                "\t* Install it somewhere (see %(home_url)s)",
            ]) % {
                'config_dir': cleanabspath(PROJECT_CONFIG_DIR, replace_home=True),
                'home_url': HOME_URL
            }
        )

    configure.tools.PATH.insert(0, configure.path.absolute(TUP_INSTALL_DIR))

    if args.tup_install or (args.install and not configure.tools.which('tup')):
        tup_install(args)

    if 'Tup' == args.generator and not configure.tools.which('tup'):
        fatal(
            '\n'.join([
                "Cannot find tup binary, your options are:",
                "\t* Just use the --tup-install flag (installed in %(config_dir)s/tup)",
                "\t* Install it somewhere (see %(home_url)s)",
            ]) % {
                'config_dir': cleanabspath(PROJECT_CONFIG_DIR, replace_home=True),
                'home_url': TUP_HOME_URL
            }
        )

    try:
        defines = parse_cmdline_variables(args.define)
        exports = parse_cmdline_variables(args.export)

        prepare_build(args, defines, exports)

    except configure.Env.VariableNotFound as e:
        fatal('\n'.join([
            "Couldn't find any variable '%s', do one of the following:" % e.name,
            "\t* Export it with: `%s=something ./configure`" % e.name,
            "\t* Define it with: `./configure -D%s=something`" % e.name,
            "\t* Define it in your project config file (%s)" % cleanjoin(PROJECT_CONFIG_DIR, PROJECT_CONFIG_FILENAME),
        ]))


if __name__ == '__main__':
    main()
