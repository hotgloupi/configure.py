ENV_DIR = env
ACTIVATE = $(ENV_DIR)/bin/activate
PIP = $(ENV_DIR)/bin/pip
BEHAVE = $(ENV_DIR)/bin/behave
COVERAGE = $(ENV_DIR)/bin/coverage
VENV = python3 -mvenv
SOURCES = $(shell find src -name '*.py')

export COVERAGE_FILE=$(PWD)/.coverage-partial
export COVERAGE_PROCESS_START=$(PWD)/.coveragerc

.PHONY:
.PHONY: all clean re \
        check check/unittests check/features \
        coverage coverage/clean coverage/tests coverage/features

all: $(PIP)
	( . $(ACTIVATE); $(PIP) install -e . )

check/tests:
	( . $(ACTIVATE); python setup.py test; )

check/features: $(BEHAVE) all
	( . $(ACTIVATE); $(BEHAVE) tests/features -q -m -k --no-capture )

check/features/fast: $(BEHAVE) all
	( . $(ACTIVATE); $(BEHAVE) tests/features -q -m -k --no-capture --tags=~slow )

check/features/wip: $(BEHAVE) all
	( . $(ACTIVATE); $(BEHAVE) tests/features -q -m -k --no-capture --tags=wip )

coverage/clean: $(COVERAGE)
	( . $(ACTIVATE); $(COVERAGE) erase )

coverage/tests: $(COVERAGE)
	( . $(ACTIVATE); $(COVERAGE) run -a --source=src/configure setup.py test )

coverage/features: $(COVERAGE) $(BEHAVE) all
	( . $(ACTIVATE); $(COVERAGE) run -a --source=src/configure $(BEHAVE) tests/features -q -m -k -T --no-summary --no-snippets --no-capture --tags=~slow --tags=~no-coverage )

coverage/report: $(COVERAGE) $(BEHAVE) all
	( . $(ACTIVATE); $(COVERAGE) combine )
	( . $(ACTIVATE); $(COVERAGE) report )

coverage: $(COVERAGE) coverage/clean coverage/tests coverage/features coverage/report

check: check/unittests check/features

$(COVERAGE): $(PIP)
	test -f $(COVERAGE) || ( . $(ACTIVATE); $(PIP) install python-coveralls )

$(BEHAVE): $(PIP)
	test -f $(BEHAVE) || ( . $(ACTIVATE); $(PIP) install git+https://github.com/behave/behave )

$(PIP): $(ENV_DIR)
	test -f $(PIP) || ( . $(ACTIVATE); python third-parties/get-pip.py )

$(ENV_DIR):
	$(VENV) --without-pip $(ENV_DIR) \
		|| ( rm -rf $(ENV_DIR) && $(VENV) $(ENV_DIR) )

clean:
	rm -rf $(ENV_DIR)

