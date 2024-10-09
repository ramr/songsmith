#!/usr/bin/env make

SRC_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))) )
PYTHONPATH := $(PYTHONPATH):$(SRC_DIR)/src

all:	build

build:	install-packages
	@echo "  - Build completed."

clean:
	@echo "  - Removing songsmith database ..."
	@rm -f data/songsmith.pickle

	@echo "  - Cleaning out virtual environment ..."
	@rm -rf "$(SRC_DIR)/.venv"

test:	tests
tests:	lint

lint:
	@echo "  - Checking shell scripts ..."
	shellcheck bin/*

	@echo "  - Linting python code ..."
	(export PYTHONPATH=$(PYTHONPATH);                           \
	 python3 -m pylint src/ bin/ --ignore-patterns=test_.*?.py  \
        )

	@echo "  - Passed all lint checks."


#
#  Helper targets.
#
env-setup:
	@echo "  - Checking environment setup ..."
	./bin/setup-env

install-packages:	env-setup
	(source .venv/bin/activate &&   \
	   python3 -m pip install -r requirements.txt)

list-outdated:	env-setup
	@echo "  - Checking for outdated packages ..."
	(source .venv/bin/activate && python3 -m pip list --outdated)


.PHONY:	build clean test tests lint
.PHONY:	env-setup install-packages list-outdated
