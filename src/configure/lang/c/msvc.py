# -*- encoding: utf-8 -*-

from configure import path, tools
from configure import Target, Command, Node

from . import compiler as c_compiler

class Compiler(c_compiler.Compiler):

    name = 'msvc'
    binary_name = 'cl.exe'
    lib_binary_name = 'lib.exe'
    link_binary_name = 'link.exe'
    object_extension = 'obj'
    as_binary_name = 'ml'

    attributes = c_compiler.Compiler.attributes + [
        ('multithread', True),
    ]

    os_env = [
        'COMSPEC',
        'DEVENVDIR',
        'EXTENSIONSDKDIR',
        'FRAMEWORK40VERSION',
        'FRAMEWORKDIR32',
        'FRAMEWORKDIR',
        'FRAMEWORKVERSION32',
        'FRAMEWORKVERSION',
        'FSHARPINSTALLDIR',
        'INCLUDE',
        'LIB',
        'LIBPATH',
        'PSMODULEPATH',
        'VCINSTALLDIR',
        'VISUALSTUDIOVERSION',
        'VS110COMNTOOLS',
        'VS120COMNTOOLS',
        'VSINSTALLDIR',
        'PATH',
        'SYSTEMDRIVE',
        'SYSTEMROOT',
        'TEMP',
        'TMP',
        'WINDIR',
        'WINDOWSSDKDIR',
        'WINDOWSSDK_EXECUTABLEPATH_X64',
        'WINDOWSSDK_EXECUTABLEPATH_X86',
    ]


    def __init__(self, build, **kw):
        kw.setdefault('lang', 'c')
        super(Compiler, self).__init__(build, **kw)
        self.lib_binary = build.find_binary(self.lib_binary_name, 'LIBEXE')
        self.link_binary = build.find_binary(self.link_binary_name, 'LINKEXE')
        self.as_binary = build.find_binary(self.as_binary_name, 'AS')

    # Prefix a flag (with '-' or '/')
    def _flag(self, flag):
        return '-' + flag

    def library_extensions(self, shared, for_linker = False):
        if for_linker:
            return self.library_extensions(shared) + self.library_extensions(not shared)
        if shared:
            return ['dll']
        else:
            return ['lib']
    @property
    def _lang_flag(self):
        return self._flag('Tc')

    def _get_build_flags(self, kw):
        tgt = kw.get('target')
        flags = [
            self._flag('nologo'),   # no print while invoking cl.exe
            self._flag('c'),        # compiles without linking
            #self._flag('GL'), # Whole program optimization (disable crt init ...)
            #self._flag('Gz'),       #__stdcall convention
            self._flag('Gd'), #__cdecl convention
            #self._flag('Gr'), #__fastcall convention
            '-GS',
            '-W3',
        ]

        defines = self.list_attr('defines', kw)[:]
        defined = lambda key: any((
            (isinstance(e, str) and e == key) or
            (isinstance(e, tuple) and e[0] == key)
        ) for e in defines)
        def define_value(key):
            for e in defines:
                if isinstance(e, tuple):
                    if e[0] == key:
                        return e[1]
            return None
        def set_default(key, value):
            for e in defines:
                if isinstance(e, tuple):
                    if e[0] == key:
                        return e[1]
            defines.append((key, value))
            return value

        if not defined('CRTAPI1'):
            defines.append(('CRTAPI1', '_cdecl'))
        if not defined('CRTAPI2'):
            defines.append(('CRTAPI2', '_cdecl'))

        if True: # XXX arch
            defines.extend([
                ('_X86', '1'),
                'WIN32',
                '_WIN32',
            ])

        defines.append('_WINNT') # XXX support for WIN95 ?

        winver = set_default('WINVER', '0x0601')
        set_default('NTDDI_VERSION', '%s0000' % winver)
        set_default('_WIN32_WINNT', winver)

        defines.append('_MT') # XXX Only multithreaded app

        # XXX debug builds not supported
        if isinstance(tgt, self.LibraryTarget):
            if tgt.shared:
                defines.append('_DLL')
            flags.extend(['-MD'])
        else:
            static_std = self.attr('static_libstd', kw)
            if static_std is not None:
                if static_std:
                    flags.append(self._flag('MT'))
                else:
                    flags.append(self._flag('MD'))

        if self.attr('enable_warnings', kw):
            flags += [
                self._flag('W3'),   # warning level (0 -> 4)
                #self._flag('WL'),   # Enables one-line diagnostics for error
                                    # and warning messages when compiling C++
                                    # source code from the command line.
            ]

        optimization = self.attr('optimization', kw)
        if optimization is not None:
            flags.append(
                self._flag({

                    self.optimize_size: 'O1s',
                    self.dont_optimize: 'Od',
                    self.optimize: 'Ot2',
                    self.optimize_harder: 'Obgt2',
                    self.optimize_fastest: 'Ox',

                }[optimization])
            )

        for dir_ in self._include_directories(kw):
            flags.extend([
                self._flag('I'),
                dir_,
            ])
        for define in defines:
            if isinstance(define, str):
                flags.extend([self._flag('D'), define])
            else:
                assert len(define) == 2
                key, val = define
                flags.append("%s%s=%s" % (self._flag('D'), key, val))
        return flags

    def _build_object_cmd(self, object, source, **kw):
        additional_outputs = []
        if source.path.endswith('.asm'):
            command = [
                self.as_binary,
                '-c',
                '-Fo' + object.path,
                source,
            ]
        else:
            command = [
                self.binary,
                self._get_build_flags(kw),
                self._lang_flag, source,
                self._flag('Fo') + object.path,
            ]
            build = self.attr('build', kw)
            if self.attr('generate_debug', kw):
                command.append(self._flag('Zi'))
                debug_db = Target(
                    build,
                    object.relative_path(build.directory) + ".pdb",
                    shell_formatter = \
                        lambda p: [self._flag('Fd') + object.path + ".pdb"]
                )
                command.append(debug_db)
                additional_outputs.append(debug_db)
        return Command(
            action = kw.get('action', "Build object"),
            target = object,
            inputs = [source],
            command = command,
            os_env = self.os_env,
            additional_outputs = additional_outputs,
        )

    def _link_flags(self, kw):
        flags = [
            #self._flag('WX'), # Linker warnings are errors
            #self._flag('LTCG'),
        ]
        dirs = []
        files = []
        system_files = []
        for library in self.list_attr('libraries', kw):
            if isinstance(library, Target):
                f = library.path
                if f.lower().endswith('.dll'):
                    f = f[:-4] + '.lib' # XXX quick fix using import lib
                files.append(f)
                dirs.append(library.dirname)
                continue
            dirs.extend(library.directories)
            if library.system:
                system_files.extend(library.files)
            else:
                for f in library.link_files:
                    assert not f.endswith('.dll')
                    files.append(f)

        dirs = tools.unique(dirs)
        flags.extend(
            Node(
                self.attr('build', kw),
                dir_,
                is_directory = True,
                shell_formatter = lambda p: [self._flag('LIBPATH:') + p],
            ) for dir_ in dirs
        )
        flags.extend(
            Node(
                self.attr('build', kw),
                f,
                shell_formatter = lambda p: [path.basename(p)]
            ) for f in files
        )
        flags.extend(system_files)
        flags.append(self.__architecture_flag(kw))
        return flags


    def _link_library_cmd(self, target, objects, shared = None, **kw):
        assert isinstance(shared, bool)
        if shared:
            cmd = [
                self.link_binary,
                self._flag('nologo'),   # no print while invoking cl.exe
                '-entry:_DllMainCRTStartup@12',
                self._flag('DLL'), # dynamic library
                self._flag('incremental:no'),
                objects,
            ]
            build = self.attr('build', kw)
            build_dir = build.directory
            no_ext_filename = target.relative_path(build_dir)[:-3]
            ao = [
                Target(build, no_ext_filename + "exp"),
                Target(build, no_ext_filename + "lib"),
            ]
            if self.attr('generate_debug', kw):
                debug_db = Target(
                    build,
                    no_ext_filename + 'pdb',
                    shell_formatter = lambda p: [
                        self._flag('PDB:') + p
                    ]
                )
                cmd.extend([
                    self._flag('DEBUG'),
                    debug_db
                ])
                ao.append(debug_db)
            cmd.extend([
                self._flag('out:') + target.relative_path(),
                self._link_flags(kw),
            ])
        else:
            cmd = [
                self.lib_binary,
                self._flag('nologo'),   # no print while invoking cl.exe
                objects,
                self._flag('out:') + target.relative_path(),
                self._link_flags(kw)
            ]
            ao = []
        return Command(
            action = "Link %s library" % (shared and "shared" or "static"),
            command = cmd,
            target = target,
            inputs = objects,
            os_env = self.os_env,
            additional_outputs= ao
        )

    def _link_executable_cmd(self, target, objects, **kw):
        build = self.attr('build', kw)
        ao = []
        cmd = [
            self.link_binary,
            self._flag('nologo'),   # no print while invoking cl.exe
            objects,
            Node(
                build,
                target.path,
                shell_formatter = lambda p: [self._flag('out:') + p]
            ),
            self._flag('subsystem:') + 'console',
            self._link_flags(kw),
        ]
        if self.attr('generate_debug', kw):
            debug_db = Target(
                build,
                target.relative_path(build.directory)[:-3] + 'pdb',
                shell_formatter = lambda p: [
                    self._flag('PDB:') + p
                ]
            )
            cmd.extend([
                self._flag('DEBUG'),
                debug_db
            ])
            ao.append(debug_db)
        return Command(
            action = "Link executable",
            command = cmd,
            target = target,
            additional_outputs = ao,
            os_env = self.os_env,
        )

    def __architecture_flag(self, kw):
        return {
            '64bit': self._flag('MACHINE:')+'x64',
            '32bit': self._flag('MACHINE:')+'x86',
        }[self.attr('target_architecture', kw)]

###############################################################################
# link.exe options
#
# @
#     Specifies a response file.
# /ALIGN
#     Specifies the alignment of each section.
# /ALLOWBIND
#     Specifies that a DLL cannot be bound.
# /ALLOWISOLATION
#     Specifies behavior for manifest lookup.
# /APPCONTAINER
#     Specifies whether the app must run within an appcontainer process
#     environment.
# /ASSEMBLYDEBUG
#     Adds the DebuggableAttribute to a managed image.
# /ASSEMBLYLINKRESOURCE
#     Creates a link to a managed resource.
# /ASSEMBLYMODULE
#     Specifies that a Microsoft intermediate language (MSIL) module should be
#     imported into the assembly.
# /ASSEMBLYRESOURCE
#     Embeds a managed resource file in an assembly.
# /BASE
#     Sets a base address for the program.
# /CLRIMAGETYPE
#     Sets the type (IJW, pure, or safe) of a CLR image.
# /CLRSUPPORTLASTERROR
#     Preserves the last error code of functions that are called through the
#     P/Invoke mechanism.
# /CLRTHREADATTRIBUTE
#     Specifies the threading attribute to apply to the entry point of your CLR
#     program.
# /CLRUNMANAGEDCODECHECK
#     Specifies whether the linker will apply the SuppressUnmanagedCodeSecurity
#     attribute to linker-generated PInvoke stubs that call from managed code
#     into native DLLs.
# /DEBUG
#     Creates debugging information.
# /DEF
#     Passes a module-definition (.def) file to the linker.
# /DEFAULTLIB
#     Searches the specified library when external references are resolved.
# /DELAY
#     Controls the delayed loading of DLLs.
# /DELAYLOAD
#     Causes the delayed loading of the specified DLL.
# /DELAYSIGN
#     Partially signs an assembly.
# /DLL
#     Builds a DLL.
# /DRIVER
#     Creates a kernel mode driver.
# /DYNAMICBASE
#     Specifies whether to generate an executable image that can be randomly
#     rebased at load time by using the address space layout randomization
#     (ASLR) feature.
# /ENTRY
#     Sets the starting address.
# /errorReport
#     Reports internal linker errors to Microsoft.
# /EXPORT
#     Exports a function.
# /FIXED
#     Creates a program that can be loaded only at its preferred base address.
# /FORCE
#     Forces a link to complete even with unresolved symbols or symbols defined
#     more than once.
# /FUNCTIONPADMIN
#     Creates an image that can be hot patched.
# /HEAP
#     Sets the size of the heap, in bytes.
# /HIGHENTROPYVA
#     Specifies support for high-entropy 64-bit address space layout
#     randomization (ASLR).
# /IDLOUT
#     Specifies the name of the .idl file and other MIDL output files.
# /IGNOREIDL
#     Prevents the processing of attribute information into an .idl file.
# /IMPLIB
#     Overrides the default import library name.
# /INCLUDE
#     Forces symbol references.
# /INCREMENTAL
#     Controls incremental linking.
# /INTEGRITYCHECK
#     Specifies that the module requires a signature check at load time.
# /KEYCONTAINER
#     Specifies a key container to sign an assembly.
# /KEYFILE
#     Specifies a key or key pair to sign an assembly.
# /LARGEADDRESSAWARE
#     Tells the compiler that the application supports addresses larger than
#     two gigabytes
# /LIBPATH
#     Enables user override of the environmental library path.
# /LTCG
#     Specifies link-time code generation.
# /MACHINE
#     Specifies the target platform.
# /MANIFEST
#     Creates a side-by-side manifest file and optionally embeds it in the
#     binary.
# /MANIFESTDEPENDENCY
#     Specifies a <dependentAssembly> section in the manifest file.
# /MANIFESTFILE
#     Changes the default name of the manifest file.
# /MANIFESTINPUT
#     Specifies a manifest input file for the linker to process and embed in
#     the binary. You can use this option multiple times to specify more than
#     one manifest input file.
# /MANIFESTUAC
#     Specifies whether User Account Control (UAC) information is embedded in
#     the program manifest.
# /MAP
#     Creates a mapfile.
# /MAPINFO
#     Includes the specified information in the mapfile.
# /MERGE
#     Combines sections.
# /MIDL
#     Specifies MIDL command-line options.
# /NOASSEMBLY
#     Suppresses the creation of a .NET Framework assembly.
# /NODEFAULTLIB
#     Ignores all (or the specified) default libraries when external references
#     are resolved.
# /NOENTRY
#     Creates a resource-only DLL.
# /NOLOGO
#     Suppresses the startup banner.
# /NXCOMPAT
#     Marks an executable as verified to be compatible with the Windows Data
#     Execution Prevention feature.
# /OPT
#     Controls LINK optimizations.
# /ORDER
#     Places COMDATs into the image in a predetermined order.
# /OUT
#     Specifies the output file name.
# /PDB
#     Creates a program database (PDB) file.
# /PDBALTPATH
#     Uses an alternate location to save a PDB file.
# /PDBSTRIPPED
#     Creates a program database (PDB) file that has no private symbols.
# /PGD
#     Specifies a .pgd file for profile-guided optimizations.
# /PROFILE
#     Produces an output file that can be used with the Performance Tools
#     profiler.
# /RELEASE
#     Sets the Checksum in the .exe header.
# /SAFESEH
#     Specifies that the image will contain a table of safe exception handlers.
# /SECTION
#     Overrides the attributes of a section.
# /STACK
#     Sets the size of the stack in bytes.
# /STUB
#     Attaches an MS-DOS stub program to a Win32 program.
# /SUBSYSTEM
#     Tells the operating system how to run the .exe file.
# /SWAPRUN
#     Tells the operating system to copy the linker output to a swap file
#     before it is run.
# /TLBID
#     Specifies the resource ID of the linker-generated type library.
# /TLBOUT
#     Specifies the name of the .tlb file and other MIDL output files.
# /TSAWARE
#     Creates an application that is designed specifically to run under
#     Terminal Server.
# /VERBOSE
#     Prints linker progress messages.
# /VERSION
#     Assigns a version number.
# /WINMD
#     Enables generation of a Windows Runtime Metadata file.
# /WINMDFILE
#     Specifies the file name for the Windows Runtime Metadata (winmd) output
#     file that's generated by the /WINMD linker option.
# /WINMDKEYFILE
#     Specifies a key or key pair to sign a Windows Runtime Metadata file.
# /WINMDKEYCONTAINER
#     Specifies a key container to sign a Windows Metadata file.
# /WINMDDELAYSIGN
#     Partially signs a Windows Runtime Metadata (.winmd) file by placing the
#     public key in the winmd file.
# /WX
#     Treats linker warnings as errors.

###############################################################################
# cl.exe options
#
# @
#     Specifies a response file.
# /?
#     Lists the compiler options.
# /AI
#     Specifies a directory to search to resolve file references passed to the
#     #using directive.
# /analyze
#     Enable code analysis.
# /arch
#     Specifies the architecture for code generation.
# /bigobj
#     Increases the number of addressable sections in an .obj file.
# /C
#     Preserves comments during preprocessing.
# /c
#     Compiles without linking.
# /clr
#     Produces an output file to run on the common language runtime.
# /D
#     Defines constants and macros.
# /doc
#     Process documentation comments to an XML file.
# /E
#     Copies preprocessor output to standard output.
# /EH
#     Specifies the model of exception handling.
# /EP
#     Copies preprocessor output to standard output.
# /errorReport
#     Allows you to provide internal compiler error (ICE) information directly
#     to the Visual C++ team.
# /F
#     Sets stack size.
# /favor
#     Produces code that is optimized for a specific x64 architecture or for
#     the specifics of micro-architectures in both the AMD64 and Extended
#     Memory 64 Technology (EM64T) architectures.
# /FA
#     Creates a listing file.
# /Fa
#     Sets the listing file name.
# /FC
#     Display full path of source code files passed to cl.exe in diagnostic
#     text.
# /Fd
#     Renames program database file.
# /Fe
#     Renames the executable file.
# /FI
#     Preprocesses the specified include file.
# /Fi
#     Sets the preprocessed output file name.
# /Fm
#     Creates a mapfile.
# /Fo
#     Creates an object file.
# /fp
#     Specify floating-point behavior.
# /Fp
#     Specifies a precompiled header file name.
# /FR
# /Fr
#     Generates browser files.
# /FU
#     Forces the use of a file name as if it had been passed to the #using
#     directive.
# /Fx
#     Merges injected code with source file.
# /G1
#     Optimize for Itanium processor. Only available in the IPF cross compiler
#     or IPF native compiler.
# /G2
#     Optimize for Itanium2 processor (default between /G1 and /G2). Only
#     available in the IPF cross compiler or IPF native compiler.
# /GA
#     Optimizes code for Windows application.
# /Gd
#     Uses the __cdecl calling convention (x86 only).
# /Ge
#     Activates stack probes.
# /GF
#     Enables string pooling.
# /GH
#     Calls hook function _pexit.
# /Gh
#     Calls hook function _penter.
# /GL
#     Enables whole program optimization.
# /Gm
#     Enables minimal rebuild.
# /GR
#     Enables run-time type information (RTTI).
# /Gr
#     Uses the __fastcall calling convention (x86 only).
# /GS
#     Buffers security check.
# /Gs
#     Controls stack probes.
# /GT
#     Supports fiber safety for data allocated using static thread-local
#     storage.
# /GX
#     Enables synchronous exception handling.
# /Gy
#     Enables function-level linking.
# /GZ
#     Same as /RTC1./RTC (Run-Time Error Checks)
# /Gz
#     Uses the __stdcall calling convention (x86 only).
# /H
#     Restricts the length of external (public) names.
# /HELP
#     Lists the compiler options.
# /homeparams
#     Forces parameters passed in registers to be written to their locations on
#     the stack upon function entry. This compiler option is only for the x64
#     compilers (native and cross compile).
# /hotpatch
#     Creates a hotpatchable image.
# /I
#     Searches a directory for include files.
# /J
#     Changes the default char type.
# /kernel
#     The compiler and linker will create a binary that can be executed in the
#     Windows kernel.
# /LD
#     Creates a dynamic-link library.
# /LDd
#     Creates a debug dynamic-link library.
# /link
#     Passes the specified option to LINK.
# /LN
#     Creates an MSIL module.
# /MD
#     Creates a multithreaded DLL using MSVCRT.lib.
# /MDd
#     Creates a debug multithreaded DLL using MSVCRTD.lib.
# /MP
#     Compiles multiple source files by using multiple processes.
# /MT
#     Creates a multithreaded executable file using LIBCMT.lib.
# /MTd
#     Creates a debug multithreaded executable file using LIBCMTD.lib.
# /nologo
#     Suppresses display of sign-on banner.
# /O1
#     Creates small code.
# /O2
#     Creates fast code.
# /Ob
#     Controls inline expansion.
# /Od
#     Disables optimization.
# /Og
#     Uses global optimizations.
# /Oi
#     Generates intrinsic functions.
# /openmp
#     Enables #pragma omp in source code.
# /Os
#     Favors small code.
# /Ot
#     Favors fast code.
# /Ox
#     Uses maximum optimization (/Ob2gity /Gs).
# /Oy
#     Omits frame pointer (x86 only).
# /P
#     Writes preprocessor output to a file.
# /Qfast_transcendentals
#     Generates fast transcendentals.
# /QIfist
#     Suppresses _ftol when a conversion from a floating-point type to an
#     integral type is required (x86 only).
# /Qimprecise_fwaits
#     Removes fwait commands inside try blocks.
# /QIPF_B
#     Does not generate sequences of instructions that give unexpected results,
#     according to the errata for the B CPU stepping. (IPF only).
# /QIPF_C
#     Does not generate sequences of instructions that give unexpected results,
#     according to the errata for the C CPU stepping. (IPF only).
# /QIPF_fr32
#     Do not use upper 96 floating-point registers. (IPF only).
# /QIPF_noPIC
#     Generates an image with position dependent code (IPF only).
# /QIPF_restrict_plabels
#     Enhances performance for programs that do not create functions at
#     runtime. (IPF only).
# /Qpar (Auto-Parallelizer)
#     Enables automatic parallelization of loops that are marked with the
#     #pragma loop() directive.
# /Qvec-report (Auto-Vectorizer Reporting Level)
#     Enables reporting levels for automatic vectorization.
# /RTC
#     Enables run-time error checking.
# /showIncludes
#     Displays a list of include files during compilation.
# /Tc
# /TC
#     Specifies a C source file.
# /Tp
# /TP
#     Specifies a C++ source file.
# /U
#     Removes a predefined macro.
# /u
#     Removes all predefined macros.
# /V
#     Sets the version string.
# /vd
#     Suppresses or enables hidden vtordisp class members.
# /vmb
#     Uses best base for pointers to members.
# /vmg
#     Uses full generality for pointers to members.
# /vmm
#     Declares multiple inheritance.
# /vms
#     Declares single inheritance.
# /vmv
#     Declares virtual inheritance.
# /volatile
#     Selects how the volatile keyword is interpreted.
# /W
#     Sets warning level.
# /w
#     Disables all warnings.
# /Wall
#     Enables all warnings, including warnings that are disabled by default.
# /WL
#     Enables one-line diagnostics for error and warning messages when
#     compiling C++ source code from the command line.
# /Wp64
#     Detects 64-bit portability problems.
# /X
#     Ignores the standard include directory.
# /Y-
#     Ignores all other precompiled-header compiler options in the current
#     build.
# /Yc
#     Creates a precompiled header file.
# /Yd
#     Places complete debugging information in all object files.
# /Yl
#     Injects a PCH reference when creating a debug library
# /Yu
#     Uses a precompiled header file during build.
# /Z7
#     Generates C 7.0–compatible debugging information.
# /Za
#     Disables language extensions.
# /Zc
#     Specifies standard behavior under /Ze./Za, /Ze (Disable Language
#     Extensions)
# /Ze
#     Enables language extensions.
# /Zg
#     Generates function prototypes.
# /ZI
#     Includes debug information in a program database compatible with Edit and
#     Continue.
# /Zi
#     Generates complete debugging information.
# /Zl
#     Removes default library name from .obj file (x86 only).
# /Zm
#     Specifies the precompiled header memory allocation limit.
# /Zp
#     Packs structure members.
# /Zs
#     Checks syntax only.
# /ZW
#     Produces an output file to run on the Windows Runtime.
