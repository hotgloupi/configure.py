from __future__ import print_function

import configure
import sys

@given('a system executable {exe}')
def step_impl(context, exe):
    if configure.tools.which(exe) is None:
        print(
            "Skipping scenario", context.scenario,
            "(executable %s not found)" % exe,
            file = sys.stderr
        )
        context.scenario.skip("The executable '%s' is not present" % exe)
    else:
        print(
            "Found executable '%s' at '%s'" % (exe, configure.tools.which(exe)),
            file = sys.stderr
        )

