# -*- encoding: utf-8 -*-

"""This file defines the default variables for your project and the configure
function.

All variable defined here will be available in the configure function, only if
their name is in the form [A-Z][_A-Z0-9]* (upper case, underscore and digits).

If a variable is evaluated to False, and if a variable with the same name but
suffixed with "_CMD" exists, it will be evaluated as follow:
    * if it is a string or a list, it launches a shell command
    * if it is a python function, it will be called with a project and a build
      instances as arguments.

For example:
     >>> VERSION_NAME = None                              # necessary
     >>> VERSION_NAME_CMD = "git --describe"              # retreive with git
     >>> VERSION_NAME_CMD = ["git", "--describe"]         # safer syntax
     >>> def myPythonFunction(project) : return 32        # simple function
     ...
     >>> VERSION_NAME_CMD = _myPythonFunction

and in the configure function, you do:
    >>> print(project.env.VERSION_NAME)

All variables defined here can be overridden by:
    * The cache (modified through ./configure -DVAR=value)
    * the OS environment

For example, if `NAME` is defined to 'original' in this script,
    >>> project.env.NAME == 'original'
    True

But, if you run:
    $ ./configure -DNAME="cached"
Then, the variable `NAME` will always be evaluated to "cached", at the opposite
of using environment:
    $ NAME="only_for_this_time" ./configure

"""

NAME = 'my_project_name'

import configure

def main(project, build):
    """ This is a configure function """

    ## Retreive BUILD_TYPE (defaults to DEBUG)
    build_type = project.env.get('BUILD_TYPE', 'DEBUG')

    ## Print a status message (Could have been verbose or debug)
    configure.tools.status("Configuring", project.env.NAME,
                      'in', build.directory, '(%s)' % build_type)


    ## Choose C++ compiler
    if platform.IS_WINDOWS:
        CXXCompiler = configure.lang.cxx.msvc.Compiler
    else:
        CXXCompiler = configure.lang.cxx.gcc.Compiler

    ## Create a new compiler
    # compiler = CXXCompiler(
    #     project,
    #     build,
    #     position_independent_code = True,
    #     standard = 'c++11',
    # )

    #configure.tools.status("CXX compiler is", compiler.binary)

    ## to link an executable, simply use the link_executable method.
    # my_program_exe = compiler.link_executable(
    #     "my_program",                 # The executable name
    #     ["src/main.cpp", ],           # source files
    #     directory = "release/bin",    # executable destination
    #     libraries=[],                 # library dependencies
    # )


    ## Or a library
    my_lib = compiler.link_library(
        'libmy_lib',
        glob("src/my_lib/*.cpp", recursive=True),
        directory  = 'release/lib',
        libraries = [],
        defines = ['MY_LIB_BUILD_DLL'],
        shared = True #and not platform.IS_MACOSX #bug with tup on macosx
    )
