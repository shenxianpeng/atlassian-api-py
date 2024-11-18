PKG_NAME = atlassian_api_py
VERSION ?= $(shell ls dist/atlassian_api_py* | cut -d - -f 2)
UNAME := $(shell uname)

ifeq ($(UNAME), Linux)
	PIP ?= pip3
	PYTHON ?= python3
else
	PIP ?= pip
	PYTHON ?= python
endif

help: ## Makefile help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install deps for development
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	pre-commit install

build: clean ## Build wheel package
	@$(PYTHON) -m pip wheel -w dist --no-deps .

install-whl: build ## Install wheel package
	@$(PIP) install dist/$(PKG_NAME)-$(VERSION)-py3-none-any.whl

clean: ## Cleanup generate files
	@rm -rf dist build $(PKG_NAME)* .mypy_cache 2>/dev/null || true

test: ## Run tests
	@cd tests && $(PYTHON) -m unittest
	@cd ..

coverage: ## Run code coverage
	@cd tests
	@coverage run -m unittest
	@echo "== Report on the results"
	@coverage report -m
	@echo "== get annotated HTML"
	@coverage html
	@cd ..

mypy: ## Check static typing
	mypy atlassian
