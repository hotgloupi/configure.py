@c
Feature: C executable

	Scenario: Hello world
		Given a project configuration
		"""
		import configure.lang.c
		def main(project, build):
			cc = configure.lang.c.find_compiler(project, build)
			cc.link_executable(
				'hello-world.exe',
				['hello-world.c']
			)
		"""
		And a source file hello-world.c
		"""
		#include <stdio.h>
		int main() { printf("Hello, world!\n"); return 0; }
		"""
		When I configure and build
		Then I can launch hello-world.exe



