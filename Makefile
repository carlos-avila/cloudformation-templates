#@IgnoreInspection BashAddShebang
##
#
# Usage
#
#   $ make            # install dependencies and compile files
#   $ make build      # compile files
#   $ make clean      # remove target files
#   $ make distclean  # remote target and build files

##
#
# Variables
#

TARGET := $(shell find src -type f -name 'template.py' -or -name '*-template.py' | sed 's/\.py/\.json/' | sed 's/^src\//dist\//')
SOURCE := $(shell find src -type f -name '*.py')

PIP_REQ := requirements.txt

##
#
# Targets
#
# The format goes:
#
#   target: list of dependencies
#     commands to build target
#
# If something isn't re-compiling double-check the changed file is in the
# target's dependencies list.
#
# Phony targets - when the target-side of a definition is just a label, not
# a file. Ensures it runs properly even if a file by the same name exists.

.PHONY: all
all: build

.PHONY: setup
setup: setup-pip

.PHONY: setup-pip
setup-pip:
	@printf '* %s\n' "installing requirements..."
	@pip install -Ur $(PIP_REQ)

.PHONY: build
build: build-templates

.PHONY: build-templates
build-templates: $(TARGET)

.PHONY: clean
clean: clean-pyc clean-build

.PHONY: clean-pyc
clean-pyc:
	@printf '* %s\n' "removing python byte code..."
	@find . -name '*.pyc' -exec rm -f {} \;
	@find . -name '*.pyo' -exec rm -f {} \;
	@find . -name '*~' -exec rm -f  {} \;

.PHONY: clean-build
clean-build:
	@printf '* %s\n' "removing built files..."
	@rm -rf dist

$(TARGET): $(SOURCE)
	@printf '* %s\n' "building $@..."
	@mkdir -p $(@D)
	@python $(shell echo $@ | sed 's/\.json/\.py/' | sed 's/^dist\//src\//' ) > $@

##
#
# Reference
#
# $@ - the target filename.
# $% - the target member name.
# $< - the filename of the first prerequisite.
# $? - space-delimited prerequisites.
# $^ - space-delimited prerequisites. Named member only for archive members.
# $+ - like $^ but prerequisites listed more than once are duplicated in the order they were listed
# $| - space-delimited order-only prerequisites.
# $* - The stem with which an implicit rule matches
# $(@D) The directory part of the file name of the target, with the trailing slash removed.
# $(@F) The file part of the file name of the target.
# $(<D) The directory part of the file name of the prerequisite, with the trailing slash removed.
# $(<F) The file part of the file name of the prerequisite.
# @ - suppress output of command.
