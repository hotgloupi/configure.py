#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import argparse
import os
import pipes
import re
import shutil
import stat
import subprocess
import sys

def cleanpath(p, **kwargs):
    p = os.path.normpath(p).replace('\\', '/')
    if p.startswith('./'):
        return p[2:]
    if kwargs.get('replace_home'):
        return os.path.join(
            '~',
            os.path.relpath(p, start=os.path.expanduser('~')),
        )
    return p

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
    paths = os.environ['PATH'].split(':')
    for dir_ in paths:
        path = os.path.join(dir_, binary)
        if os.path.exists(path) and os.stat(path)[stat.ST_MODE] & stat.S_IXUSR:
            return path
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
ROOT_DIR = cleanpath(os.path.dirname(__file__))
HOME_URL = "http://hotgloupi.fr/tupcfg.html"
TUP_HOME_URL = "http://gittup.org"
PROJECT_CONFIG_DIR_NAME = ".config"
PROJECT_CONFIG_DIR = cleanjoin(ROOT_DIR, PROJECT_CONFIG_DIR_NAME)
PROJECT_CONFIG_FILENAME = "project.py"
TUP_INSTALL_DIR = cleanjoin(PROJECT_CONFIG_DIR, 'tup')
TUP_GIT_URL = "git://github.com/gittup/tup.git"
TUPCFG_INSTALL_DIR = cleanjoin(PROJECT_CONFIG_DIR, 'tupcfg-install')
TUPCFG_GIT_URL = "git://github.com/hotgloupi/tupcfg.git"
MAKEFILE_TEMPLATE = """
.PHONY:
.PHONY: all

all: %(tup_config_dir)s
	@sh -c 'cd %(root_dir)s && %(tup_bin)s upd'

%(tup_config_dir)s:
	@sh -c 'cd %(root_dir)s && %(tup_bin)s init'

monitor: %(tup_config_dir)s
	@sh -c 'export PATH=%(project_config_dir)s/tup:$$PATH; cd %(root_dir)s && %(tup_bin)s monitor -f -a'

"""

def self_install(args):
    status("Installing tupcfg in", TUPCFG_INSTALL_DIR)
    if not os.path.exists(TUPCFG_INSTALL_DIR):
        os.makedirs(TUPCFG_INSTALL_DIR)
        status("Getting tup from", TUPCFG_GIT_URL)
        cmd(['git', 'clone', TUPCFG_GIT_URL, TUPCFG_INSTALL_DIR])
    else:
        status("Updating tup")
        cmd(['git', 'pull'], cwd=TUPCFG_INSTALL_DIR)
    shutil.rmtree(os.path.join(PROJECT_CONFIG_DIR, 'tupcfg'), ignore_errors=True)
    shutil.copytree(
        os.path.join(TUPCFG_INSTALL_DIR, 'src/tupcfg'),
        os.path.join(PROJECT_CONFIG_DIR, 'tupcfg')
    )


def tup_install(args):
    status("Installing tup in", TUP_INSTALL_DIR)
    if not os.path.exists(TUP_INSTALL_DIR):
        os.makedirs(TUP_INSTALL_DIR)
        status("Getting tup from", TUP_GIT_URL)
        cmd(['git', 'clone', TUP_GIT_URL, TUP_INSTALL_DIR])
    else:
        status("Updating tup")
        cmd(['git', 'pull'], cwd=TUP_INSTALL_DIR)

    if not which('tup'):
        cmd(['sh', 'build.sh'], cwd=TUP_INSTALL_DIR)

    tup_dir = os.path.join(ROOT_DIR, '.tup')
    if os.path.exists(tup_dir):
        os.rename(tup_dir, tup_dir + '.bak')

    try:
        if not os.path.exists(os.path.join(TUP_INSTALL_DIR, '.tup')):
            cmd(['./build/tup', 'init'], cwd=TUP_INSTALL_DIR)
        cmd(['./build/tup', 'upd'], cwd=TUP_INSTALL_DIR)
    finally:
        if os.path.exists(tup_dir + '.bak'):
            os.rename(tup_dir + '.bak', tup_dir)


def prepare_build(build_dir, defines):
    import tupcfg # Should work at this point
    from os.path import exists, join, abspath

    tup_build_marker = join(build_dir, '.tupcfg_build')

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


    try:
        project = tupcfg.Project(
            ROOT_DIR,
            PROJECT_CONFIG_DIR,
            config_filename = PROJECT_CONFIG_FILENAME,
        )
        build = tupcfg.Build(build_dir)
        project.configure(build, new_vars=defines)

    except tupcfg.Project.NeedUserEdit:
        print(
            "Please edit %s and re-run the configure script" % cleanjoin(
                PROJECT_CONFIG_DIR,
                PROJECT_CONFIG_FILENAME,
                replace_home=True,
            )
        )
        sys.exit(0)

    makefile = join(build_dir, 'Makefile')
    with open(makefile, 'w') as f:
        f.write(MAKEFILE_TEMPLATE % {
            'tup_config_dir': abspath(cleanjoin(ROOT_DIR, '.tup')),
            'tup_bin': abspath(cleanjoin(PROJECT_CONFIG_DIR, 'tup/tup')),
            'root_dir': cleanabspath(ROOT_DIR),
            'project_config_dir': abspath(PROJECT_CONFIG_DIR),
        })

    if not exists(cleanjoin(ROOT_DIR, '.tup')):
        cmd = ['make', '-C', build_dir]
        print('Just run `%s`' % ' '.join(map(pipes.quote, cmd)))
    pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="Configure your project for tup"
    )
    parser.add_argument('build_dir', action="store",
                        help="Where to build your project",
                        nargs='*')
    parser.add_argument('-D', '--define', action='append',
                        help="Define build specific variables", default=[])
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose mode")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('--dump', action='store_true', help="dump build variables")
    parser.add_argument('--install', action='store_true', help="install when needed")
    parser.add_argument('--self-install', action='store_true', help="install (or update) tupcfg")
    parser.add_argument('--tup-install', action='store_true', help="install (or update) tup")

    #parser.add_argument('--release', action='store_true')
    #parser.add_argument('--version-major', type=int, default=VERSION_MAJOR)
    #parser.add_argument('--version-name', default=VERSION_NAME)
    #parser.add_argument('--version-minor', type=int, default=VERSION_MINOR)
    #parser.add_argument('--version-hash', default=VERSION_HASH)
    #parser.add_argument('--tup-bin', default=which('tup'))
    #parser.add_argument('--dc-bin', default=(which('dmd') or which('gdc') or which('ldc')))
    return parser, parser.parse_args()


def main():
    parser, args = parse_args()

    DEBUG = args.debug
    VERBOSE = args.verbose

    from os.path import exists, join

    sys.path.insert(0, PROJECT_CONFIG_DIR)

    have_tupcfg = False
    try:
        import tupcfg
        have_tupcfg = True
    except: pass

    if args.self_install or (args.install and not have_tupcfg):
        self_install(args)
        try:
            import tupcfg
        except:
            fatal("Sorry, tupcfg installation failed for some reason.")

    try:
        import tupcfg

        # Tupcfg will use these functions to log
        tupcfg.tools.status = status
        tupcfg.tools.error = error
        tupcfg.tools.fatal = fatal

        tupcfg.tools.DEBUG = DEBUG
        tupcfg.tools.VERBOSE = VERBOSE
    except ImportError as err:
        if DEBUG is True:
            raise err

        fatal(
            '\n'.join([
                "Cannot find tupcfg module, your options are:",
                "\t* Just use the --self-install flag (installed in %(config_dir)s/tupcfg)",
                "\t* Install it somewhere (see %(home_url)s)",
            ]) % {
                'config_dir': cleanabspath(PROJECT_CONFIG_DIR, replace_home=True),
                'home_url': HOME_URL
            }
        )

    os.environ['PATH'] = ':'.join(
        [os.path.abspath(TUP_INSTALL_DIR)] + os.environ['PATH'].split(':')
    )

    if args.tup_install or (args.install and not tupcfg.tools.which('tup')):
        tup_install(args)

    if not tupcfg.tools.which('tup'):
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

    if not args.build_dir:
        err(FATAL, "No build directory specified on command line.")
        parser.print_usage()
        sys.exit(1)

    try:
        for build_dir in args.build_dir:
            defines = {}
            for d in args.define:
                k, v = d.split('=')
                defines[k.strip()] = v.strip()
            prepare_build(build_dir, defines)

    except tupcfg.Env.VariableNotFound as e:
        fatal('\n'.join([
            "Couldn't find any variable '%s', do one of the following:" % e.name,
            "\t* Export it with: `%s=something ./configure`" % e.name,
            "\t* Define it with: `./configure -D%s=something`" % e.name,
            "\t* Define it in your project config file (%s)" % cleanjoin(PROJECT_CONFIG_DIR, PROJECT_CONFIG_FILENAME),
        ]))


if __name__ == '__main__':
    main()
