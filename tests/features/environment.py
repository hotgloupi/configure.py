import tempfile
import shutil

def before_all(ctx):
    ctx.directory = tempfile.mkdtemp()

def after_all(ctx):
    shutil.rmtree(ctx.directory, ignore_errors = True)
