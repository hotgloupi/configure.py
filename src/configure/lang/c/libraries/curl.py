
from configure.dependency.cmake import CMakeDependency
from configure import platform
from configure.dependency import Dependency
from configure.command import Command
from configure.target import Target

class CURLDependencyMSVC(Dependency):
    def __init__(self,
                 build,
                 compiler,
                 source_directory,
                 zlib = None,
                 openssl = None,
                 with_cookies = True,
                 with_crypto_auth = True,
                 with_dict = True,
                 with_file = True,
                 with_ftp = True,
                 with_http = True,
                 with_ldap = True,
                 with_ldaps = True,
                 with_telnet = True,
                 with_tftp = True,
                 use_ares = False,
                 hidden_visibility = True,
                 shared = True):
        super().__init__(
            build,
            name = 'curl',
            source_directory = source_directory,
        )
        command = [
            'nmake', '/f', 'Makefile.vc',
            'ENABLE_IDN=no', 'ENABLE_WINSSL=no', 'GEN_PDB=no', 'DEBUG=no',
            'mode=%s' % (shared and 'dll' or 'static'),
        ]
        dir = 'src/builds/libcurl-vc-x86-release-%(mode)s-ipv6-sspi-spnego' % {
            'mode': shared and 'dll' or 'static',
        }
        if shared:
            lib = dir + '/bin/libcurl.dll'
            lnk = dir + '/lib/libcurl.lib'
        else:
            lib = dir + '/lib/libcurl_a.lib'
            lnk = lib
        target = Target(self.build, self.build_path(lib))
        self.targets = [
            Command(
                "Building %s" % self.name,
                target = target,
                additional_outputs = [],
                command = command,
                working_directory = self.build_path('src/winbuild'),
                inputs = build.fs.copy_tree(
                    self.source_path(),
                    dest = self.build_path('src')
                ),
                os_env = compiler.os_env,
            ).target
        ]
        self.libraries = [
            compiler.Library(
                self.name,
                compiler,
                shared = shared,
                search_binary_files = False,
                include_directories = [self.absolute_source_path('include')],
                directories = [self.absolute_build_path(dir, 'lib')],
                files = [self.absolute_build_path(lib)],
                link_files = [self.absolute_build_path(lnk)],
                save_env_vars = False,
            )
        ]

class CURLDependencyCMake(CMakeDependency):

    def __init__(self,
                 build,
                 compiler,
                 source_directory,
                 zlib = None,
                 openssl = None,
                 idn = None,
                 with_cookies = True,
                 with_crypto_auth = True,
                 with_dict = True,
                 with_file = True,
                 with_ftp = True,
                 with_http = True,
                 with_ldap = True,
                 with_ldaps = True,
                 with_telnet = True,
                 with_tftp = True,
                 use_ares = False,
                 hidden_visibility = True,
                 shared = True):
        if not with_ldap or not openssl:
            with_ldaps = False
        if not openssl:
            with_crypto_auth = False
        configure_variables = [
            ('CURL_ZLIB', bool(zlib)),
            ('CMAKE_USE_OPENSSL', bool(openssl)),
            ('CURL_DISABLE_COOKIES', not with_cookies),
            ('CURL_DISABLE_CRYPTO_AUTH', not with_crypto_auth),
            ('CURL_DISABLE_DICT', not with_dict),
            ('CURL_DISABLE_FILE', not with_file),
            ('CURL_DISABLE_FTP', not with_ftp),
            ('CURL_DISABLE_HTTP', not with_http),
            ('CURL_DISABLE_LDAP', not with_ldap),
            ('CURL_DISABLE_LDAPS', not with_ldaps),
            ('CURL_DISABLE_TELNET', not with_telnet),
            ('CURL_DISABLE_TFTP', not with_tftp),
            ('CURL_USE_ARES', use_ares),
            ('HIDDEN_VISIBILITY', hidden_visibility),
        ]
        if not shared:
            configure_variables.append(('CURL_STATICLIB', True))
        super().__init__(
            build,
            "cURL",
            compiler = compiler,
            source_directory = source_directory,
            libraries = [
                {
                    'prefix': 'lib',
                    'name': 'curl',
                    'shared': shared,
                    'imp_filename': (shared and compiler.name == 'msvc') and 'libcurl_imp.lib' or 'libcurl.lib',
                }
            ],
            configure_variables = configure_variables
        )
        if not shared and platform.IS_LINUX:
            if idn is not None:
                self.libraries.extend(idn.libraries)
            else:
                from configure.lang import c
                self.libraries.append(c.libraries.simple('idn', compiler, system = True))


if platform.IS_WINDOWS and False:
    CURLDependency = CURLDependencyMSVC
else:
    CURLDependency = CURLDependencyCMake
