ENV_DIR = env
ACTIVATE = $(ENV_DIR)/bin/activate
PIP = $(ENV_DIR)/bin/pip
BEHAVE = $(ENV_DIR)/bin/behave
VENV = python3 -mvenv
SOURCES = $(shell find src -name '*.py')

.PHONY:
.PHONY: all clean re check check/fast

all: $(PIP)
	( . $(ACTIVATE); $(PIP) install -e . )

check/fast:
	( . $(ACTIVATE); python setup.py test; )
	( . $(ACTIVATE); $(BEHAVE) tests/features -q -m )

$(BEHAVE):
	test -f $(BEHAVE) || ( . $(ACTIVATE); $(PIP) install behave )

check: all $(BEHAVE) check/fast

$(PIP): $(ENV_DIR)
	test -f $(PIP) || ( . $(ACTIVATE); python third-parties/get-pip.py )

$(ENV_DIR):
	$(VENV) --without-pip $(ENV_DIR) \
		|| ( rm -rf $(ENV_DIR) && $(VENV) $(ENV_DIR) )

clean:
	rm -rf $(ENV_DIR)

