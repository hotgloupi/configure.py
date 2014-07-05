@c
Feature: C library

	Scenario: Creating static library
		Given a source file my.c
		"""
		int my() { return 42; }
		"""
		And a source file test.c
		"""
		int my();
		int main() {
			if (my() == 42) return 0;
			return 1;
		}
		"""
		And a project configuration
		"""
		from configure.lang.c import find_compiler
		def main(project, build):
			cc = find_compiler(project, build)
			my = cc.link_static_library(
				'libmy',
				['my.c']
			)
			cc.link_executable(
				'test.exe',
				['test.c'],
				libraries = [my],
			)
		"""
		When I configure and build
		Then I can launch test.exe

	Scenario: Creating dynamic library
		Given a source file my.c
		"""
		int my() { return 42; }
		"""
		And a source file test.c
		"""
		int my();
		int main() {
			if (my() == 42) return 0;
			return 1;
		}
		"""
		And a project configuration
		"""
		from configure.lang.c import find_compiler
		def main(project, build):
			cc = find_compiler(project, build)
			my = cc.link_dynamic_library(
				'libmy',
				['my.c'],
				hidden_visibility = False,
			)
			cc.link_executable(
				'test.exe',
				['test.c'],
				libraries = [my],
			)
		"""
		When I configure and build
		Then I can launch test.exe
