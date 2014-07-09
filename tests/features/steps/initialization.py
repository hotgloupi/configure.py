import os
import shlex
import sys

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
    assert context.initialized

@given('an empty project')
def step_impl(ctx):
    ctx.execute_steps(
        '''
        Given a project configuration
        """
        def main(build):
            pass
        """
        '''
    )

@then('configure failed')
def step_impl(context):
    assert not context.initialized

@when('I launch configure --init')
def step_impl(context):
    context.initialized = context.cmd('configure', '--init') == 0

@when('I configure the build')
def step_impl(context):
    context.configured = context.cmd('configure', 'build') == 0

@then('A .config directory is created')
def step_impl(context):
    assert context.initialized
    assert os.path.isdir('.config')

@then('a project config file is created')
def step_impl(context):
    assert context.initialized
    assert os.path.isfile('.config/project.py')

@given('a project configuration')
def step_impl(context):
    context.execute_steps("Given an initialized directory")
    assert context.text is not None
    assert context.initialized
    with open(".config/project.py", 'w') as f:
        f.write(context.text)


@given('a source file {filename}')
@when('a source file {filename}')
def step_impl(context, filename):
    with open(filename, 'w') as f:
        f.write(context.text)

@when('I build everything')
def step_impl(context):
    assert context.configured
    context.built = context.cmd('make', '-C', 'build') == 0

@then('I can launch {exe}')
def step_impl(context, exe):
    assert context.built
    assert context.cmd(os.path.join(context.directory, 'build', exe)) == 0

@when('I configure and build')
def step_impl(context):
    context.execute_steps(
        """
        When I configure the build
        And I build everything
        """
    )

@when('I configure with {args}')
def impl(context, args):
    context.configured = context.cmd('configure', 'build', *tuple(shlex.split(args))) == 0
