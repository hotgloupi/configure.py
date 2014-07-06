@c
Feature: Header dependencies are honored

	Scenario: Simple macro change
		Given a source file test.c
		"""
		#include "test.h"
		int main()
		{ return (ANSWER == 42 ? 0 : 1); }
		"""
		And a source file test.h
		"""
		#define ANSWER 32
		"""
		And a project configuration
		"""
		def main(build):
			from configure.lang.c import find_compiler
			find_compiler(build).link_executable('test.exe', ['test.c'])
		"""
		When I configure and build
		And a source file test.h
		"""
		#define ANSWER 42
		"""
		And I build everything
		Then I can launch test.exe

	Scenario: Indirect include
		Given a source file test.c
		"""
		#include "test.h"
		int main()
		{ return (ANSWER == 42 ? 0 : 1); }
		"""
		And a source file test.h
		"""
		#include "answer.h"
		"""
		And a source file answer.h
		"""
		#define ANSWER 32
		"""
		And a project configuration
		"""
		def main(build):
			from configure.lang.c import find_compiler
			find_compiler(build).link_executable('test.exe', ['test.c'])
		"""
		When I configure and build
		And a source file answer.h
		"""
		#define ANSWER 42
		"""
		And I build everything
		Then I can launch test.exe
