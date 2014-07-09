Feature: Configure can install itself

	Scenario:
		Given an empty project
		When I configure with --self-install
		Then .config/configure.py is a directory

	Scenario: Auto install tup
		Given an empty project
		When I configure with --tup-install
		Then .config/tup/tup is executable
