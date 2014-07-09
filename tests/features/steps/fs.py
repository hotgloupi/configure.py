import os
import configure

@then('{path} is a directory')
def impl(ctx, path):
    assert os.path.isdir(path)

@then('{path} does not exist')
def impl(ctx, path):
    assert not os.path.exists(path)

@then('{path} is executable')
def impl(ctx, path):
    assert configure.path.is_executable(path)
