import os
import subprocess

@given('a temporary directory')
def step_impl(context):
    assert os.path.isdir(context.directory)
    os.chdir(context.directory)

@when('I launch configure')
def step_impl(context):
    subprocess.check_call(['configure', '--init'])

@then('A .config directory is created')
def step_impl(context):
    assert os.path.isdir('.config')

