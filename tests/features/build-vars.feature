Feature: Configure build variables

	Scenario: Build variable
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with build test_var=LOL
		Then build variable TEST_VAR in build equals "LOL"

	Scenario: Project variable
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with build -Dtest_var=LOL
		Then project variable TEST_VAR equals "LOL"

	Scenario: Build variable precedence
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with -Dtest_var=PIF test_var=LOL build
		Then build variable TEST_VAR in build equals "LOL"
		And project variable TEST_VAR equals "PIF"

	Scenario: Set variable to multiple builds
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with test_var=LOL build1 build2
		Then build variable TEST_VAR in build1 equals "LOL"
		And build variable TEST_VAR in build2 equals "LOL"

	Scenario: Command line variable after the build
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with build test_var=LOL
		Then build variable TEST_VAR in build equals "LOL"

	Scenario: Command line project variable after the build
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with build -Dtest_var=LOL
		Then project variable TEST_VAR equals "LOL"

	Scenario: Command line project variable after the build and a build variable
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with build test_var=LOL -Dtest_var=LOL
		Then project variable TEST_VAR equals "LOL"
		And build variable TEST_VAR in build equals "LOL"


