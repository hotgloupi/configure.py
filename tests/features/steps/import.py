import os
import sys

from behave import given, when, then

@given('configure.py is in the PYTHONPATH')
def configure_is_in_pythonpath(ctx):
    for d in sys.path:
        path = os.path.join(d, 'configure', '__init__.py')
        if os.path.exists(path):
            return
    assert False, "Couldn't find configure.py in sys.path"

@when('I import configure')
def import_configure(ctx):
    ctx.configure = __import__('configure')

@then('configure.py has been imported')
def configure_has_been_imported(ctx):
    assert ctx.configure is not None

