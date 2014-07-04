ENV_DIR = env
ACTIVATE = $(ENV_DIR)/bin/activate
PIP = $(ENV_DIR)/bin/pip
BEHAVE = $(ENV_DIR)/bin/behave
VENV = python3 -mvenv
SOURCES = $(shell find src -name '*.py')
#INSTALL = $(patsubst src/%.py, $(VENV_DIR)/%.py, $(SOURCES))

.PHONY:
.PHONY: all clean re check

all: $(PIP)
	( . $(ACTIVATE); $(PIP) install -e . )

check: $(ENV_DIR)
	test -f $(BEHAVE) || ( . $(ACTIVATE); $(PIP) install behave )
	( . $(ACTIVATE); python setup.py test; )
	( . $(ACTIVATE); $(BEHAVE) tests/features )

$(PIP): $(ENV_DIR)
	test -f $(PIP) || ( . $(ACTIVATE); python third-parties/get-pip.py )

$(ENV_DIR):
	$(VENV) --without-pip $(ENV_DIR)

clean:
	rm -rf $(ENV_DIR)

