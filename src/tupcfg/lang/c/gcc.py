# -*- encoding: utf-8 -*-

import sys
import pipes

from tupcfg import Target, path, tools, platform
from . import compiler as c_compiler

class Compiler(c_compiler.Compiler):

    name = 'gcc'
    binary_name = 'gcc'
    ar_binary_name = 'ar'

    __standards_map = {
        'c99': 'c99',
    }

    def __init__(self, project, build, **kw):
        kw.setdefault('lang', 'c')
        super(Compiler, self).__init__(project, build, **kw)
        self.ar_binary = tools.find_binary(self.ar_binary_name, project.env, 'AR')
        project.env.project_set('AR', self.ar_binary)

    def _get_build_flags(self, cmd):
        flags = []
        pic = self.attr('position_independent_code', cmd)
        if pic and not platform.IS_WINDOWS:
            flags.append('-fPIC')
        if self.attr('hidden_visibility', cmd):
            flags.append('-fvisibility=hidden')
            flags.append('-fvisibility-inlines-hidden')
        if self.attr('enable_warnings', cmd):
            flags.extend(['-Wall', '-Wextra'])

        if self.attr('use_build_type_flags', cmd):
            if self.project.env['BUILD_TYPE'].upper() == 'DEBUG':
                flags.append('-g3')
            else:
                flags.append('-O2')

        std = self.attr('standard', cmd)
        if std:
            flags.append('-std=%s' % self.__standards_map[std])

        defines = cmd.kw.get('defines', []) + self.defines
        for define in defines:
            if isinstance(define, str):
                flags.append('-D' + define)
            else:
                assert len(define) == 2 #key, value
                flags.append('-D%s=%s' % define)

        return flags + list(
            ['-I', i] for i in self._include_directories(cmd)
        )

    def _build_object_cmd(self, cmd, target=None, build=None):
        assert len(cmd.dependencies) == 1
        return [
            self.binary,
            self.__architecture_flag(cmd),
            self._get_build_flags(cmd),
            '-c', cmd.dependencies[0],
            '-o', target,
        ]

    def _build_object_dependencies_cmd(self, cmd, target=None, build=None):
        class ObjectTarget:
            def __init__(self, target):
                self.target = target
            def shell_string(self, cwd=None, build=None):
                return self.target.shell_string(cwd=cwd, build=build)

        return [
            self.binary,
            self.__architecture_flag(cmd),
            self._get_build_flags(cmd),
            '-c', cmd.source,
#            '-o', ObjectTarget(cmd.target),
            '-MM',
            '-MT', ObjectTarget(cmd.target),
            '-MF', target,
        ]

    def _generate_precompiled_header(self, source, **kw):
        return self.BuildObject(self, source, **kw)


    def __add_rpath(self, lib, **kw):
        return '-Wl,-rpath=\\$ORIGIN/' + path.dirname(lib.relpath(kw['target'], **kw))

    def _get_link_flags(self, cmd):
        library_directories = self.library_directories[:]
        link_flags = []
        pic = self.attr('position_independent_code', cmd)
        if pic and not platform.IS_WINDOWS:
            link_flags.append('-fPIC')
        if self.attr('hidden_visibility', cmd):
            link_flags.append('-fvisibility=hidden')
            link_flags.append('-fvisibility-inlines-hidden')

        if self.attr('use_build_type_flags', cmd):
            if self.project.env['BUILD_TYPE'].upper() == 'DEBUG':
                link_flags.append('-g3')
            else:
                link_flags.append('-O2')
        class RPathFlag:
            def __init__(self):
                self.libs = []
                self.directories = []

            def shell_string(self, cwd=None, build=None):
                dirs = self.directories
                for lib in self.libs:
                    dirs.append(path.dirname(path.absolute(lib.path(build))))
                dirs = tools.unique(dirs)
                if platform.IS_MACOSX:
                    return list(('-Wl,-rpath,%s' % d) for d in dirs)
                if dirs:
                    return '-Wl,-rpath,' + ':'.join(dirs)
                return ''

        rpath = RPathFlag()
        for lib in cmd.kw.get('libraries', []):
            if isinstance(lib, Target):
                link_flags.append(lib)
                rpath.libs.append(lib)
            elif not lib.macosx_framework:
                for f in lib.files:
                    if not platform.IS_MACOSX:
                        if lib.shared:
                            link_flags.append('-Wl,-Bdynamic')
                        else:
                            link_flags.append('-Wl,-Bstatic')
                    link_flags.append(f)
                for dir_ in lib.directories:
                    library_directories.append(dir_)
            else:
                link_flags.extend(['-framework', lib.name])

                #for name in lib.names:
                #    if not platform.IS_MACOSX:
                #        if lib.shared:
                #            link_flags.append('-Wl,-Bdynamic')
                #        else:
                #            link_flags.append('-Wl,-Bstatic')
                #    if platform.IS_MACOSX and lib.macosx_framework:
                #        link_flags.extend(['-framework', name])
                #    else:
                #        link_flags.append('-l%s' % name)

        if not platform.IS_MACOSX:
            link_flags.append('-Wl,-Bdynamic')
        rpath.directories.extend(library_directories)
        link_flags.append(rpath)
        link_flags.extend(self.additional_link_flags.get(self.name, []))
        return list(('-L%s' % l) for l in tools.unique(library_directories)) + link_flags

    def _link_executable_cmd(self, cmd, target=None, build=None):
        return [
            self.binary,
            cmd.dependencies,
            self.__architecture_flag(cmd),
            '-o', target,
            self._get_link_flags(cmd)
        ]

    def _link_library_cmd(self, cmd, target=None, build=None):
        if cmd.shared:
            name = path.basename(target.path(build))
            if platform.IS_MACOSX:
                link_flag = 'dynamiclib'
                soname_flag = 'install_name'
                name = '@rpath/' + name
            else:
                link_flag = 'shared'
                soname_flag = 'soname'
            return [
                self.binary,
                '-%s' % link_flag,
                self.__architecture_flag(cmd),
                cmd.dependencies,
                ('-Wl,-%s,' % soname_flag) + name,
                '-o', target,
                self._get_link_flags(cmd)
            ]
        else:
            return [
                self.ar_binary,
                'rcs',
                target,
                cmd.dependencies,
            ]

    def __architecture_flag(self, cmd):
        if self.force_architecture is False:
            return []
        return {
            '64bit': '-m64',
            '32bit': '-m32',
        }[self.attr('architecture', cmd)]
