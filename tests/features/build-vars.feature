Feature: Configure build variables

	Scenario: Simple string variable
		Given a project configuration
		"""
		def main(build):
			assert build.env.TEST_VAR == "LOL"
		"""
		When I configure with test_var=LOL
		Then build variable TEST_VAR equals "LOL"
