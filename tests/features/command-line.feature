Feature: Exercise configure command line

	@wip
	Scenario: Select one build out of multiple
		Given a project configuration
		"""
		def main(build):
			pass
		"""
		When I configure with build1 build2
		And I configure with build1 test=build_one
		And I configure with build2 test=build_two
		Then build variable TEST in build1 equals "build_one"
		Then build variable TEST in build2 equals "build_two"

