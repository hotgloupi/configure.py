import os
import subprocess
import behave

DEVNULL = open('/dev/null', 'wb')

@given('a temporary directory')
def step_impl(context):
    assert os.path.isdir(context.directory)

@given('an initialized directory')
def step_impl(context):
    context.execute_steps(
        '''
        Given a temporary directory
        When I launch configure --init
        '''
    )
    assert context.configured

@then('configure failed')
def step_impl(context):
    assert not context.configured

@when('I launch configure --init')
def step_impl(context):
    context.configured = subprocess.call(
        ['configure', '--init'],
        stdout = DEVNULL, stderr = DEVNULL
    ) == 0

@then('A .config directory is created')
def step_impl(context):
    assert context.configured
    assert os.path.isdir('.config')

@then('a project config file is created')
def step_impl(context):
    assert context.configured
    assert os.path.isfile('.config/project.py')

