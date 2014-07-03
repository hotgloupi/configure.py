
Feature: Initialize project file

	Scenario: Launch configure script
		Given a temporary directory
		When I launch configure
		Then A .config directory is created

	Scenario: Launch script in readonly directory
		Given a directory
		When I launch configure
		Then I got errors
