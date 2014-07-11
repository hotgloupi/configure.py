Feature: Handle correctly created build directories

	Scenario: Remember previously configured build directory
		Given an initialized directory
		When I configure with build
		And the build is configured
		Then I configure
		And the build is configured

	Scenario: Configure multiple builds
		Given an initialized directory
		When I configure with build1 build2 build3
		Then build1 is a directory
		And build2 is a directory
		And build3 is a directory
