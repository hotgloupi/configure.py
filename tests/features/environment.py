from __future__ import print_function # beeing nice with jedi-vim

import copy
import os
import shutil
import subprocess
import sys
import tempfile

from behave.log_capture import capture

def cmd(*args, **kw):
    process = subprocess.Popen(
        args,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        **kw
    )
    while process.returncode is None:
        out, err = process.communicate()
        out, err = out.decode('utf8'), err.decode('utf8')
        print(out)
        print(err, file = sys.stderr)
    return process.returncode

def before_all(ctx):
    ctx.cmd = cmd
    ctx.disable_coverage = False
    def _cmd(*args, **kw):
        if ctx.disable_coverage:
            env = copy.deepcopy(kw.get('env', os.environ))
            env.pop('COVERAGE_PROCESS_STARTUP', None)
            env.pop('COVERAGE_FILE', None)
            kw['env'] = env
        return cmd(*args, **kw)
    ctx.cmd = _cmd

def before_tag(ctx, tag):
    if tag == 'no-coverage':
        ctx.disable_coverage = True

def after_tag(ctx, tag):
    ctx.disable_coverage = False

def before_scenario(ctx, scenario):
    ctx.directory = tempfile.mkdtemp(prefix = 'configure.py-%s-' % scenario.name.replace(' ', ''))
    ctx.old_cwd = os.getcwd()
    os.chdir(ctx.directory)

@capture
def after_scenario(ctx, scenario):
    if scenario.status == "failed" and \
       os.getenv('KEEP_FAILURES', 'no').lower() in ('1', 'yes', 'true'):
        print("KEEPING DIRECTORY", ctx.directory, 'OF FAILED SCENARIO', scenario)
    else:
        shutil.rmtree(ctx.directory, ignore_errors = True)
    os.chdir(ctx.old_cwd)


