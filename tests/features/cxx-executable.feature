@cxx
Feature: C++ executable

	Scenario Outline: Hello world
		Given a system executable <compiler>
		And a project configuration
		"""
		from configure.lang.cxx import find_compiler
		from configure.tools import status
		def main(build):
			cxx = find_compiler(build, name = "<compiler>", standard = 'c++03')
			status("Found CXX compiler", cxx.binary)
			cxx.link_executable(
				'hello-world',
				['hello-world.cpp']
			)
		"""
		And a source file hello-world.cpp
		"""
		#include <iostream>
		int main() { std::cout << "Hello, world!\n"; return 0; }
		"""
		When I configure and build
		Then I can launch hello-world

		Examples: C++ compilers
			| compiler |
			| g++     |
			| g++-4.7 |
			| g++-4.8 |
			| clang++ |
			| cl.exe |
