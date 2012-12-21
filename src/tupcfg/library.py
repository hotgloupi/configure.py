# -*- encoding: utf-8 -*-

from . import tools
from . import path

class Library:

    # These variables are used in the _prepare_variables function.
    variable_names = [
        ('prefixes', 'prefix'),
        ('include_directories', 'include_directory'),
        ('directories', 'directory'),
    ]

    def __init__(self,
                 name,
                 compiler,
                 prefixes = [],
                 include_directories = [],
                 include_directory_names = [''],
                 directories = [],
                 name_suffixes = None,
                 shared = False,
                 macosx_framework = False,
                 find_includes = [],
                 use_system_paths = True,
                 search_binary_files = True):
        self.name = name
        self.compiler = compiler
        self.shared = shared
        self.macosx_framework = macosx_framework
        self.use_system_paths = use_system_paths
        assert isinstance(find_includes, list)
        self.find_includes = find_includes

        assert len(include_directory_names) > 0
        self.include_directory_names = include_directory_names

        self.name_suffixes = name_suffixes
        self.env = self.compiler.project.env
        self.prefixes = tools.unique(self._env_prefixes() + prefixes)
        tools.debug(self.name, "library prefixes:", self.prefixes)
        self.include_directories = self._find_include_directories(include_directories)
        tools.debug(self.name, "library include directories:", self.include_directories)
        if search_binary_files:
            self._set_directories_and_files(directories)
        else:
            self.files = self._env_files()
            self.directories = self._env_directories() + directories
        tools.debug(self.name, "library directories:", self.directories)
        tools.verbose(self.name, "library files:", ', '.join(("'%s'" % f) for f in self.files))
        self._save_env()

    @property
    def names(self):
        return [self.name]

    def _env_varname(self, name):
        return self.name.upper() + '_' + name.upper()

    def env_var(self, name, type=None):
        res = self.env.get(self._env_varname(name), type=type)
        tools.debug('retreive var:', self._env_varname(name), '=', res)
        return res

    def _save_env(self):
        self.env.build_set(self._env_varname('prefixes'), self.prefixes)
        self.env.build_set(self._env_varname('directories'), self.directories)
        self.env.build_set(self._env_varname('include_directories'), self.include_directories)
        prefix = self.shared and 'SHARED' or 'STATIC'
        self.env.build_set(self._env_varname('%s_FILES' % prefix), self.files)
        assert self.files == self.env_var('%s_FILES' % prefix, type=list)
        tools.debug("Saving %s files" % self.name, self.files)


    def _env_list(self, singular, plural):
        dir_ = self.env_var(singular)
        dirs = dir_ is not None and [dir_] or []
        return dirs + self.env_var(plural, type=list)

    def _env_include_directories(self):
        return self._env_list('include_directory', 'include_directories')

    def _env_directories(self):
        return self._env_list('directory', 'directories')

    def _env_files(self):
        prefix = self.shared and 'SHARED' or 'STATIC'
        return self.env_var('%s_FILES' % prefix, type=list)

    def _env_prefixes(self):
        return self._env_list('prefix', 'prefixes')

    def _set_directories_and_files(self, directories):
        self.directories = list(d for d in self._env_directories() if path.exists(d))
        self.files = list(f for f in self._env_files() if path.exists(f))
        if self.directories and self.files:
            tools.debug("Found %s library directories and files from environment" % self.name)
            return

        tools.debug("Searching %s library directories and files" % self.name)
        dirs = self.directories + directories
        if self.use_system_paths:
            dirs += self.library_system_paths()
        for p in self.prefixes:
            dirs.append(path.join(p, 'lib'))

        dirs = list(d for d in tools.unique(dirs) if path.exists(d))
        self.directories = []
        self.files = []

        for dir_ in dirs:
            tools.debug("Checking %s library directory '%s'" % (self.name, dir_))
            files = tools.find_files(
                working_directory = dir_,
                name = self.name,
                prefixes = ['lib'],
                extensions = self.compiler.library_extensions(self.shared),
                suffixes = self.name_suffixes,
                recursive = False,
            )
            if files:
                tools.debug("Found %s library files [%s] in directory '%s'" % (
                    self.name,
                    ', '.join(files),
                    dir_,
                ))
                self.files.extend(path.absolute(dir_, f) for f in files)
                self.directories.append(dir_)
        if not self.files:
                tools.fatal(
                    "Cannot find %s library files:" % self.name,
                    "\t* Set 'directories' when creating the library",
                    "\t* Set the environment variable '%s_DIRECTORY'" % self.name.upper(),
                    "\t* Set the environment variable '%s_DIRECTORIES'" % self.name.upper(),
                    sep='\n'
                )

    def _find_include_directories(self, include_directories):
        env_dirs = self._env_include_directories()
        if not self.find_includes:
            return tools.unique(self._env_include_directories() + include_directories)
        all_found = True
        for include in self.find_includes:
            all_found = any(
                path.exists(dir_, include) for dir_ in env_dirs
            )
            tools.debug("Search '%s':" % include, all_found)
            if not all_found: break

        if all_found:
            tools.debug("Include directories for", self.name, "found in env variables")
            return env_dirs
        tools.debug("Include directories for", self.name, "not found in env variables")
        results = []
        include_directories += env_dirs
        for p in self.prefixes:
            include_directories.append(path.join(p, 'include'))
        if self.use_system_paths:
            include_directories += self.include_system_paths()
        tools.debug("Search include directories for library", self.name)

        dirs = []
        for directory_name in self.include_directory_names:
            dirs.extend(path.join(dir_, directory_name) for dir_ in include_directories)
        include_directories = tools.unique(dirs)

        for include in self.find_includes:
            dirname, basename = path.split(include)
            name, ext = path.splitext(basename)
            found = False
            for dir_ in include_directories:
                tools.debug("Searching '%s' in directory '%s'" % (include, dir_))
                files = tools.find_files(
                    working_directory = path.join(dir_, dirname),
                    name = name,
                    extensions = [ext],
                    recursive = False,
                )
                if files:
                    found = True
                    tools.verbose("Found %s header '%s' in '%s'" % (self.name, include, dir_))
                    results.append(dir_)
                    break
            if not found:
                tools.fatal(
                    "Cannot find include file '%s' for library %s:" % (include, self.name),
                    "\t* Set 'include_directories' when creating the library",
                    "\t* Set the environment variable '%s_INCLUDE_DIRECTORY'" % self.name.upper(),
                    "\t* Set the environment variable '%s_INCLUDE_DIRECTORIES'" % self.name.upper(),
                    sep='\n'
                )
        return results


    def include_system_paths(self):
        return [
            '/usr/include',
        ]

    def library_system_paths(self):
        return [
            '/usr/lib',
            '/usr/lib/x86_64-linux-gnu',
        ]

