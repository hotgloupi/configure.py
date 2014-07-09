# -*- encoding: utf-8 -*-

from configure import tools
from configure import path
from configure import platform

import os

class Library:

    def __init__(self,
                 name,
                 compiler,
                 prefixes = [],
                 include_directories = [],
                 include_directory_names = [''],
                 files = [],
                 link_files = None,
                 directories = [],
                 binary_file_names = None,
                 name_prefixes = ['lib', ''],
                 name_suffixes = None,
                 shared = None,
                 preferred_shared = True,
                 macosx_framework = False,
                 search_macosx_framework_files = False,
                 find_includes = [],
                 use_system_paths = True,
                 search_binary_files = True,
                 only_one_binary_file = True,
                 save_env_vars = True,
                 system = False):
        self.name = name
        self.compiler = compiler
        self.env = self.compiler.build.env
        self.binary_file_names = binary_file_names
        self.name_suffixes = name_suffixes
        self.name_prefixes = name_prefixes
        self.compiler = compiler
        self.shared = shared
        self.preferred_shared = self.env_var(
            "SHARED",
            default = preferred_shared,
        )
        self.macosx_framework = macosx_framework
        self.use_system_paths = use_system_paths
        self.only_one_binary_file = only_one_binary_file
        self.system = system
        if self.system:
            search_binary_files = False
            search_macosx_framework_files = False
        assert isinstance(find_includes, list)
        self.find_includes = find_includes

        assert len(include_directory_names) > 0
        self.include_directory_names = include_directory_names

        self.prefixes = tools.unique(self._env_prefixes() + prefixes)

        self.libraries = [self]
        if self.macosx_framework and not search_macosx_framework_files:
            self.include_directories = []
            self.directories = []
            tools.debug("Files search for", self.name, "framework is not enabled.")
            return

        tools.debug(self.name, "library prefixes:", self.prefixes)
        self.include_directories = self._find_include_directories(include_directories)
        tools.debug(self.name, "library include directories:", self.include_directories)
        if search_binary_files:
            self._set_directories_and_files(directories)
        elif self.compiler.name == 'msvc' and self.system:
            self.files = [self.name + '.lib'] # + self.compiler.library_extension(self.shared)]
            self.directories = []
        else:
            self.files = self._env_files() + files
            self.directories = self._env_directories() + directories

        if link_files is None:
            if self.compiler.name == 'msvc':
                self.link_files = [
                    (path.splitext(f)[0] + '.lib') for f in self.files
                ]
            else:
                self.link_files = files[:]
        else:
            self.link_files = link_files[:]
        tools.debug(self.name, "library directories:", self.directories)
        tools.verbose(self.name, "library files:", ', '.join(("'%s'" % f) for f in self.files))
        if save_env_vars:
            self._save_env()

    @property
    def names(self):
        return [self.name]

    @property
    def targets(self):
        """Libraries are compatible with dependencies, but have no target"""
        return []

    def _env_varname(self, name):
        return self.name.upper() + '_' + name.upper()

    def env_var(self, name, default=None):
        res = self.env.get(self._env_varname(name), default=default)
        tools.debug('retreive var:', self._env_varname(name), '=', res)
        return res

    def _save_env(self):
        self.env[self._env_varname('prefixes')] = self.prefixes
        self.env[self._env_varname('directories')] = self.directories
        self.env[self._env_varname('include_directories')] = self.include_directories
        if self.shared is not None:
            prefix = self.shared and 'SHARED' or 'STATIC'
            self.env[self._env_varname('%s_FILES' % prefix)] = self.files
            assert self.files == self.env_var('%s_FILES' % prefix)
        tools.debug("Saving %s files" % self.name, self.files)


    def _env_list(self, singular, plural):
        dir_ = self.env_var(singular)
        dirs = dir_ is not None and [dir_] or []
        dirs += self.env_var(plural, [])
        dir_ = self.env.get(singular.upper())
        dirs += dir_ is not None and [dir_] or []
        dirs += self.env.get(plural.upper(), [])
        return tools.unique(path.clean(d) for d in dirs)


    def _env_prefixes(self):
        return self._env_list('prefix', 'prefixes')

    def _env_include_directories(self):
        return self._env_list('include_directory', 'include_directories')

    def _env_directories(self):
        return self._env_list('directory', 'directories')

    def _env_files(self):
        if self.shared is not None:
            prefix = self.shared and 'SHARED_' or 'STATIC_'
        else:
            prefix = ''
        return self.env_var('%sFILES' % prefix, default = [])

    def _set_directories_and_files(self, directories):
        dirs = self._env_directories()
        files = self._env_files()

        if dirs and files:
            self.directories = dirs
            self.files = files
            tools.debug("Found %s library directories and files from environment" % self.name)
            return
        else:
            self.directories = []
            self.files = []

        tools.debug("Searching %s library directories and files" % self.name)
        dirs.extend(directories)
        if self.macosx_framework:
            dirs.extend(path.join(p, 'Library', 'Frameworks') for p in self.prefixes)
        else:
            dirs.extend(path.join(p, 'lib') for p in self.prefixes)
        if self.use_system_paths:
            dirs.extend(self.library_system_paths())

        if self.macosx_framework:
            dirs = (path.join(dir_, self.name + '.framework', 'Libraries') for dir_ in dirs)

        dirs = list(path.clean(d) for d in tools.unique(dirs) if path.exists(d))

        if self.binary_file_names is not None:
            names = self.binary_file_names
        else:
            names = [self.name]

        extensions_list = []
        if self.macosx_framework:
            extensions_list = [None]
        if self.shared is not None:
            extensions_list = [
                (
                    self.shared,
                    self.compiler.library_extensions(
                        self.shared,
                        for_linker = True,
                    )
                )
            ]
        else:
            extensions_list = [
                (
                    self.preferred_shared,
                    self.compiler.library_extensions(self.preferred_shared, for_linker = True)
                ),
                (
                    not self.preferred_shared,
                    self.compiler.library_extensions(not self.preferred_shared, for_linker = True)
                ),
            ]

        for name in names:
            files = []
            for shared, extensions in extensions_list:
                for dir_ in dirs:
                    files.extend(self._find_files(dir_, name, extensions))
                    if files and self.only_one_binary_file:
                        if self.shared is None:
                            self.shared = shared
                        files = files[:1]
                        tools.debug("Stopping search for %s library files." % name)
                        break
                if files:
                    break # do not mix shared and non shared extensions


            if not files:
                    tools.fatal(
                        "Cannot find %s library files:" % self.name,
                        "\t* Set 'directories' when creating the library",
                        "\t* Set the environment variable '%s_DIRECTORY'" % self.name.upper(),
                        "\t* Set the environment variable '%s_DIRECTORIES'" % self.name.upper(),
                        "\t* Set the environment variable '%s_PREFIX'" % self.name.upper(),
                        "\t* Set the environment variable '%s_PREFIXES'" % self.name.upper(),
                        "\t* Set the environment variable 'PREFIX'",
                        "\t* Set the environment variable 'PREFIXES'",
                        "NOTE: Directories checked: %s" % ', '.join(dirs),
                        sep='\n'
                    )
            else:
                self.files.extend(files)
                self.directories.extend(path.dirname(f) for f in files)

    def _find_files(self, directory, name, extensions):
        tools.debug("Searching for {%s}%s{%s}.%s library files in directory '%s'" % (
            str(self.name_prefixes), name,
            str(self.name_suffixes),
            str(extensions),
            directory
        ))
        files = tools.find_files(
            working_directory = directory,
            name = name,
            prefixes = self.name_prefixes,
            extensions = extensions,
            suffixes = self.name_suffixes,
            recursive = False,
        )
        if files:
            tools.debug("Found {%s}%s{%s} library files [%s] in directory '%s'" % (
                str(self.name_prefixes), name, str(self.name_suffixes),
                ', '.join(files),
                directory,
            ))
            files = list(path.absolute(directory, f) for f in files)
        return files

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
                    "\t* Set the environment variable '%s_PREFIX'" % self.name.upper(),
                    "\t* Set the environment variable '%s_PREFIXES'" % self.name.upper(),
                    "\t* Set the environment variable 'PREFIX'",
                    "\t* Set the environment variable 'PREFIXES'",
                    sep='\n'
                )
        return results


    def include_system_paths(self):
        return [
            '/usr/include',
        ]

    def library_system_paths(self):
        libs = []
        if platform.IS_WINDOWS:
            libs.extend([
                {
                    '32bit': path.join(os.environ['WINDIR'], 'System32'),
                    '64bit': path.join(os.environ['WINDIR'], 'SysWOW64'),
                }[self.compiler.target_architecture],
            ])
        elif platform.IS_MACOSX:
            if self.macosx_framework:
                libs.extend([
                    "/System/Library/Frameworks",
                    "/Library/Frameworks",
                ])
        elif platform.IS_LINUX:
            libs.extend(
                {
                    '32bit': ['/lib/i386-linux-gnu', '/usr/lib/i386-linux-gnu'],
                    '64bit': ['/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu'],
                }[self.compiler.target_architecture]
            )
        libs.append('/usr/lib')
        return libs

