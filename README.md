*configure.py*
===========

**Configure your project's builds in Python.**

Generate files used to build a project and its dependencies. The list of
implemented generators (Makefiles and Tupfiles) and supported platforms
(Windows, OS X and Linux) is intented to grow, especially towards mobile and
embedded platforms.

Motivations
-----------

  * Makefiles are slow and a pain to maintain.
  * AutoTools and CMake languages are huge pain.
  * MSVC and XCode are not usable beside their native platforms.
  * CMake lacks a [Tup](http://gittup.org/tup/ "Tup home page") generator.

Tup is by design one of the fastest build system, but as it is langage
agnostic, it doesn't have a clue about library location, compiler version or
any high level system configuration. I initially solved this problem with dirty
scripts for each project using Tup, and after getting tired of maintaining
those scripts, I made up this small project that saves me a lot of time.

Features
--------

*configure.py* is written in pure Python3, and should work on any platform that
support python3. It has been successfully tested on Linux, MacOSX and Windows.

It lets you configure your projects in Python3 and generate for you files
required to build your project (like Makefiles).

Support currently:

   * Main C/C++ compilers (gcc, clang and msvc)
   * Find and link with system libraries
   * Build your project dependencies
   * Simple filesystem operations and file generations

Overview
--------

After adding and launching the configure script in your project root directory
(see GettingStarted), you end up with something like that:

    my_project/
    ├── .config
    │   ├── project.py
    ├── configure.py*
    ├── include
    │   └── my_project.h
    └── src
        └── main.c

The file `.config/project.py` contains the rules to build your project. This
file will be used to prepare one or more build directories by the `configure.py`
script.

Getting started
---------------

### Installation

Just drop the
[configure.py](https://github.com/hotgloupi/configure.py/blob/master/bin/configure) script
in the root directory of your project.

On unices, you could do:

    $ cd /path/to/your/project
    $ wget 'https://github.com/hotgloupi/configure.py/raw/master/bin/configure' -O configure
    $ chmod +x configure

This script is written in python3, so you'll obviously need python3 on your
computer. If the python executable does not use python3, you may want to change
the first line of the configure script. But I would recommend that you set
python3 as the default python version :).

The configure script will ensure that:
  * You have *Tup* executable somewhere
  * the *configure.py* python package is available

You can install yourself these two dependencies, or let the configure script
install them for you.

    $ ./configure --self-install --tup-install

Note that same flags could be used later to upgrade *configure.py* and *Tup*.

You are now asked to manually edit the file `.config/project.py`, which defines
your project rules.

### The project file

The `.config/project.py` file must define the following function:

    def main(project, build):
        print("Configuring build", build.directory)

This function is called for each build directory and is in charge of adding
targets to the build.  For the purpose of this Getting started section, let's
do a simple executable.

    from configure.lang.c import gcc

    def main(project, build):
        compiler = gcc.Compiler(project, build)
        compiler.link_executable('test', ['main.c'])

Assuming you have source file named `main.c` at the root of your project, for
example:

    #include <stdio.h>

    int main()
    {
        printf("Hello, world!\n");
        return 0;
    }

You can now configure your project in a build directory `build`

    $ ./configure build
    Configuring build
    Just run `make -C build`

The first output line comes from our `configure()` function, while the second
only appears when a build directory is created. Now, your project should be
something like that:

    $ tree .
    ├── build
    │   ├── Makefile
    │   └── Tupfile
    ├── configure
    └── main.c

    1 directory, 4 files

The makefile `build/Makefile` is generated for convinience by the configure
script.  It just call the `tup` executable, which is located in
`.config/tup/tup` when installed automatically. The `Tupfile` is generated at
the end of the `main()` function (by adding targets).

As suggested, just run `make -C build` and enjoy the magic :)

The configure script
--------------------

### Synopsis

    $ ./configure --help
    usage: configure [-h] [-D DEFINE] [-E EXPORT] [-v] [-d] [--dump-vars]
                     [--dump-build] [--install] [--self-install] [--tup-install]
                     [build_dir]

    Configure your project for tup

    positional arguments:
      build_dir             Where to build your project

    optional arguments:
      -h, --help            show this help message and exit
      -D DEFINE, --define DEFINE
                          Define build specific variables
      -E EXPORT, --export EXPORT
                          Define project specific variables
      -v, --verbose       verbose mode
      -d, --debug         debug mode
      --dump-vars         dump variables
      --dump-build        dump commands that would be executed
      --install           install when needed
      --self-install      install (or update) configure.py
      --tup-install       install (or update) tup

### The build directories

You can specify one or more directories where to build your project. The main
idea is to give you the ability to create *variants*. If you do not specify any
build directory, all build directories are configured.

### Defining variables

You can define some variables for the whole project or for specific builds with
-E and -D.  Note that the -D flags applies on all build specified on the
command line, or all project builds when none are specified.

#### Build and project variables

For example, we can do the following:

    $ ./configure build-debug -D BUILD_TYPE=DEBUG
    $ ./configure build-release -D BUILD_TYPE=RELEASE

the `BUILD_TYPE` variable is specific to each build directory. Now, if you do

    $ ./configure -D CXX=clang++

The `CXX` variable is applied on all existing build directory (previously
configured). Which is different than:

    $ ./configure -E CXX=clang++

Which is global to the project, and all build (future ones too) will inherit this
variable, and possibly override it with a build specific one.

#### Typed variables and command line operator syntax

Variables are strongly typed, but they all conveniently default to be of type
strings.  Available types are bool, string, and list of strings.

    # v1, v2, v3 and v4 are all booleans and equal to True
    $ ./configure -D v1 -D v2=TRUE -D v3=true -D v4=1

This implies that `TRUE`, `FALSE`, `YES`, `NO`, `1` and `0` are reserved values with the meaning
of a boolean (not case sensitive).

     # All other strings are simply strings.
     $ ./configure -D PROJECT_NAME=my_project

     # We can concatenate strings with '+=' operator
     $ ./configure -D PROJECT_NAME+=-v0.1 # PROJECT_NAME == my_project-v0.1

Lists are differentiated by the character `[`, their values are separated by a
comma `,`.

     # lists are recognized with '[', which need to be escaped
     $ ./configure -D PREFIXES=\[/usr, /usr/local/]

     # You can extend a list with +=
     $ ./configure -D PREFIXES+=\[/opt/local]

     # If you want to append one element, you can use := operator
     $ ./configure -D PREFIXES:=/some/prefix

Note that all of those commands will create a variable of type list, even
if it does not exist.

#### Undefining variables

To remove a variable you can just set it to nothing:

     $ ./configure -D BUILD_VAR= -E PROJECT_VAR=

This will remove `BUILD_VAR` from build variables (here, for all configured
builds), and remove `PROJECT_VAR` from the project variables.

#### Internals

Project variables are saved in the file `.config/.project_vars`, whereas build
variables are stored in their respective directory in a file named
`.build_vars`.

They contain a python dictionary that could be read or modified with the
`pickle` python module.

    >>> import pickle
    >>> pickle.loads(open('.config/.project_vars', 'rb').read())

You can easily dump all project and builds variables using the `--dump-vars`
flag.

### Dumping the build

While this is mainly a debug functionality, dumping all targets can be of a
great help in some cases. Use `--dump-build` when you feel it :)

### Auto install everything

As seen previously the `--tup-install` and `--self-install` flags force the
installation or the update of *Tup* and *configure.py*. To install only when
tup or configure.py are not found, use the `--install` flag instead.

configure.py core
-----------

Before getting into the facilities that *configure.py* offers, you should know a little
about the core objects used to define rules.

### Everything is a `Node`

The `Node` class is very simple: it only has a `dependencies` attribute. Almost
every other classes inherit it.

### `Source` class

The `Source` class is a `Node` with no dependencies. it just has a `filename`
attribute, which is relative to the root directory.

### `Command` class

The `Command` class is a `Node` that has the ability to generate a shell command
for a target. While its dependencies are known at construction time, the target
is only given through its method `command(target, build)`, which returns the
shell command.

### `Target` class

The `Target` class is a `Node` that as name, which is the output filename
relative to the build directory by default. Its dependencies are mostly
commands.


### A simple example

Let's do a simple command that copy a file:

    import configure

    class CopyFile(configure.Command):
        def __init__(self, dependencies):
            # We just ensure that we are copying only one file at a time
            assert len(dependencies) == 1
            # Call the parent constructor
            super(CopyFile, self).__init__(dependencies)

        # Returns an expressive string about the action
        @property
        def action(self):
            return "Copying %s to" % self.dependencies[0]

        # Returns a list that represent the shell command
        def command(self, target=None, build=None):
            assert target is not None
            return ['cp', self.dependencies[0], target]

We can use this command class whenever we want to copy a file.

    def configure(project, build):
        resource = configure.Source("resources/images/file1.jpg")
        copy = CopyFile(resource)
        target = configure.Target("resources/images/file1.jpg", copy)
        build.add_target(target)

Of course, you can generalise, factorise and improve the copy of files in many
ways, but you see here what's involved. Note that the file path is relative to
the project root for the `Source` instance, and relative to the build root for
the `Target` instance. The directory components are automatically created during
the configuration.

