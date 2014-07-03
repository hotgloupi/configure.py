Feature: Import configure.py library

Scenario: Import configure module
		Given configure.py is in the PYTHONPATH
		When I import configure
		Then configure.py has been imported

