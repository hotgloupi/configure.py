
from configure.lang.c import find_compiler

def main(build):
    cc = find_compiler(build)
    cc.link_executable('test.exe', ['test.c'])
