.PHONY: clean clean-test clean-pyc clean-build docs help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style
	uv run ruff check glean_parser tests
	uv run ruff format --check glean_parser tests
	uv run yamllint glean_parser tests
	uv run mypy glean_parser

fmt: ## autoformat files
	uv run ruff format glean_parser tests

test: ## run tests quickly with the default Python
	uv run pytest

test-full:  ## run tests, including those with additional dependencies
	uv run pytest --run-web-tests --run-node-tests --run-ruby-tests --run-go-tests  --run-rust-tests

coverage: ## check code coverage quickly with the default Python
	uv run coverage run --source glean_parser -m pytest
	uv run coverage report -m
	uv run coverage html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/glean_parser.rst
	rm -f docs/modules.rst
	uv run sphinx-apidoc -o docs/ glean_parser
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

release: dist ## package and upload a release
	uv publish

dist: clean ## builds source and wheel package
	uv build

install: clean ## install the package to the active Python's site-packages
	uv sync

install-kotlin-linters: ## install ktlint and detekt for linting Kotlin output
	test -f ktlint || curl -sSLO https://github.com/shyiko/ktlint/releases/download/0.29.0/ktlint
	echo "03c9f9f78f80bcdb44c292d95e4d9abf221daf5e377673c1b6675a8003eab94d *ktlint" | shasum -a256 -c -
	chmod a+x ktlint
	test -f detekt-cli.jar || curl -sSL --output "detekt-cli.jar" https://github.com/detekt/detekt/releases/download/v1.23.6/detekt-cli-1.23.6-all.jar
	echo "898dcf810e891f449e4e3f9f4a4e2dc75aecf8e1089df41a42a69adb2cbbcffa *detekt-cli.jar" | shasum -a256 -c -
