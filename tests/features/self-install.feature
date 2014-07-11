Feature: Configure can install itself

	@no-coverage @slow
	Scenario:
		Given an empty project
		When I configure with build --self-install
		Then .config/configure.py is a directory

	@tup @slow
	Scenario: Auto install tup
		Given an empty project
		When I configure with build --tup-install
		Then .config/tup/tup is executable
