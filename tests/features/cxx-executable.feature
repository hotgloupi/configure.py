@cxx
Feature: C++ executable

	Scenario: Hello world
		Given a project configuration
		"""
		import configure.lang.cxx
		def main(project, build):
			cxx = configure.lang.cxx.find_compiler(project, build)
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
