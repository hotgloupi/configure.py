
from configure.dependency.cmake import CMakeDependency
from configure import platform

class CURLDependency(CMakeDependency):

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
                }
            ],
            configure_variables = configure_variables
        )
        if not shared and platform.IS_LINUX:
            from configure.lang import c
            self.libraries.append(c.libraries.simple('idn', compiler, system = True))

