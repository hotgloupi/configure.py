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

    def __init__(self, build = None):
        """Constructor for the generator.

        Assign `build' and `project' attributes.
        """
        assert build is not None
        self.project = build.project
        self.build = build

    def __call__(self, node):
        """Visit node"""
        raise Exception("NotImplemented")

    def __enter__(self):
        """Starting generation by calling begin()."""
        self.begin()
        return self

    def __exit__(self, type_, value, traceback):
        """Finalize generation by calling close() if no error happened."""
        if type_ is None:
            self.end()

    def begin(self): pass
    def end(self): pass

