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

def err(*args, **kwargs):
    kwargs['file'] = sys.stderr
    return print(*args, **kwargs)

def fatal(*args, **kwargs):
    try:
        err(*args, **kwargs)
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
    import pipes
    print('Run: %s' % ' '.join(map(pipes.quote, cmd)), file = sys.stderr)
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

VERBOSE = True
ROOT_DIR = cleanpath(os.path.dirname(__file__))
HOME_URL = "http://hotgloupi.fr/tupcfg.html"
TUP_HOME_URL = "http://gittup.org"
TUP_GIT_URL = "git://github.com/gittup/tup.git"
PROJECT_CONFIG_DIR_NAME = ".config"
PROJECT_CONFIG_DIR = cleanjoin(ROOT_DIR, PROJECT_CONFIG_DIR_NAME)
PROJECT_CONFIG_FILENAME = "project.py"
TUP_INSTALL_DIR = cleanjoin(PROJECT_CONFIG_DIR, 'tup')

def parse_args():
    parser = argparse.ArgumentParser(
        description="Configure your project for tup"
    )
    parser.add_argument('build_dir', action="store",
                        help="Where to build your project",
                        nargs='?', default=None)
    parser.add_argument('-D', '--define', action='append',
                        help="Define build specific variables")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose mode")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('--dump', action='store_true', help="dump build variables")
    parser.add_argument('--self-install', action='store_true', help="install (or update) tupcfg")
    parser.add_argument('--tup-install', action='store_true', help="install (or update) tup")

    #parser.add_argument('--release', action='store_true')
    #parser.add_argument('--version-major', type=int, default=VERSION_MAJOR)
    #parser.add_argument('--version-name', default=VERSION_NAME)
    #parser.add_argument('--version-minor', type=int, default=VERSION_MINOR)
    #parser.add_argument('--version-hash', default=VERSION_HASH)
    #parser.add_argument('--tup-bin', default=which('tup'))
    #parser.add_argument('--dc-bin', default=(which('dmd') or which('gdc') or which('ldc')))
    return parser.parse_args()

def self_install(args):
    pass

def tup_install(args):
    print("Installing tup in", TUP_INSTALL_DIR)
    if not os.path.exists(TUP_INSTALL_DIR):
        os.makedirs(TUP_INSTALL_DIR)
        print("Getting tup from", TUP_GIT_URL)
        cmd(['git', 'clone', TUP_GIT_URL, TUP_INSTALL_DIR])
    else:
        print("Updating tup")
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



if __name__ == '__main__':
    args = parse_args()

    if args.self_install:
        self_install(args)
        import tupcfg

    try:
        import tupcfg
    except ImportError:
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

    if args.tup_install:
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

    if args.build_dir is None:
        fatal("Please specify a build directory")

    try:
        project = tupcfg.Project(
            ROOT_DIR,
            PROJECT_CONFIG_DIR,
            config_filename = PROJECT_CONFIG_FILENAME,
        )
        build = tupcfg.Build(args.build_dir)
        project.configure(build)

    except tupcfg.Project.NeedUserEdit:
        print(
            "Please edit %s and re-run the configure script" % cleanjoin(
                PROJECT_CONFIG_DIR,
                PROJECT_CONFIG_FILENAME,
                replace_home=True,
            )
        )

    makefile = os.path.join(args.build_dir, 'Makefile')
    with open(makefile, 'w') as f:
        f.write('\n'.join([
            "all: %(tup_config_dir)s",
            "\t@sh -c 'cd %(root_dir)s && %(tup_bin)s upd'",
            "",
            "%(tup_config_dir)s:",
            "\t@sh -c 'cd %(root_dir)s && %(tup_bin)s init'",
        ]) % {
            'tup_config_dir': os.path.abspath(cleanjoin(ROOT_DIR, '.tup')),
            'tup_bin': os.path.abspath(cleanjoin(PROJECT_CONFIG_DIR, 'tup/tup')),
            'root_dir': cleanabspath(ROOT_DIR),
        } + '\n')

    if not os.path.exists(cleanjoin(ROOT_DIR, '.tup')):
        cmd = ['make', '-C', args.build_dir]
        print('Just run `%s`' % ' '.join(map(pipes.quote, cmd)))

