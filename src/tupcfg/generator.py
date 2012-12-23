# -*- encoding: utf-8 -*-

class Generator:
    """Generator base class.

    A generator is created for each build. When discovering a directory where
    targets will be build, a `with' statement is done on that directory: The
    `__call__' method is called with the working directory as only parameter,
    and `__enter__' method is fired right after that. Then, its method
    `apply_rule' is called for each target with all information needed to
    create a corresponding creation rule. When all rules are processed, the
    `__exit__' method is fired. Note that both `__call__' and `__enter__' are
    meant to be overriden, but they should return continue to return `self'.

    Finally, when everything has been done for the build, the `close' method is
    called.

    Each method has a simple default behavior except `apply_rule' which has to
    be overridden.
    """

    def __init__(self, project=None, build=None):
        """Constructor for the generator.

        Assign `build' and `project' attributes.
        """
        assert project is not None
        assert build is not None
        self.project = project
        self.build = build

    def __call__(self, working_directory=None):
        """Assign `working_directory' attribute."""
        assert working_directory is not None
        self.working_directory = working_directory
        return self

    def __enter__(self):
        """Entering in a new build working directory."""
        return self

    def __exit__(self, type_, value, traceback):
        """Finalize a working directory."""
        pass

    def apply_rule(self,
                   action=None,
                   command=None,
                   inputs=None,
                   additional_inputs=None,
                   outputs=None,
                   additional_ouputs=None,
                   target=None):
        """Apply a rule to create the target.

        parameters:
            action: A string for the rule
            command: A list of the shell command to create the target
            inputs: A list of input files (instance of `Source`)
            additional_inputs: Additionl input files (inputs that are generated elsewhere but implicitly used)
            outputs: The output files (contains the target instance)
            additional_outputs: Additional output files (implicitly created)
            target: The `Target` instance represent the file to be created
        """
        raise Exception("Not implemented")

    def close(self):
        """Finalize a build generation."""
        pass

