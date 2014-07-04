import tempfile
import shutil
import os

def before_scenario(ctx, scenario):
    ctx.directory = tempfile.mkdtemp()
    ctx.old_cwd = os.getcwd()
    os.chdir(ctx.directory)

def after_scenario(ctx, scenario):
    shutil.rmtree(ctx.directory, ignore_errors = True)
    os.chdir(ctx.old_cwd)

