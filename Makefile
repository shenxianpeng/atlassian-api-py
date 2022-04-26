##################################################################
# 					   Release Checklist                         #
##################################################################
# 1. Manually update `version` in setup.py and README.md         #
# 2. All tests pass.                      run `make test`        #
# 3. Generate build.                      run `make build`       #
# 4. Upload to testpypi if need testing.  run `make test-pypi`   #
# 5. Upload to pypi for release.          run `make pypi`        #
# 6. Create tag and push to remote.       run `make push-tag`    #
##################################################################
PKG_NAME ?= atlassian_api_py
VERSION ?= $(shell grep version setup.py | cut -d "=" -f2 | cut -d "," -f1)
UNAME := $(shell uname)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD  2>&1)

ifeq ($(UNAME), Linux)
	PIP ?= pip3
	PYTHON ?= python3
else
	PIP ?= pip
	PYTHON ?= python
endif

help: ## Makefile help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check_wheel:
	@echo "Check wheel file"
	@ls dist/$(PKG_NAME)-$(VERSION)-py3-none-any.whl

check_branch:
ifneq ($(BRANCH),master)
	@echo "Please release from master branch. exit."
	@exit 1
endif
	@echo "== Check branch passed ✅"

build: clean ## Make package
	@echo "== Start to build $(PKG_NAME) package"
	@$(PYTHON) setup.py bdist_wheel # add sdist if need
	@echo "== Build Succeeded ✅"

install: build ## Install package
	@echo "== Start to install $(PKG_NAME) package"
	@$(PIP) install dist/$(PKG_NAME)-$(VERSION)-py3-none-any.whl
	@echo "== Install Succeeded ✅"

clean: ## Cleanup generate files
	@echo "== Star to clean generate files"
	@rm -rf dist build
	@echo "== Cleanup Succeeded ✅"

lint: ## Lint python code
	@echo "== Start to lint python code"
	@black .
	@echo "== Lint Succeeded ✅"

pypi: build ## Upload to pypi
	@echo "== Start to upload $(PKG_NAME) to https://pypi.org/"
	@rm ~/.pypirc 2>/dev/null || true
	@twine upload dist/*
	@echo "== Upload PyPI Succeeded ✅"

test-pypi: build ## Upload to test-pypi
	@echo "== Start to upload $(PKG_NAME) to https://test.pypi.org/"
	@twine upload --repository testpypi dist/*
	@echo "== Upload Test PyPI Succeeded ✅"

tag: ## Create git tag on local
	@echo "== Start to make $(PKG_NAME) tag v$(VERSION)"
	@git tag -d v$(VERSION) 2>/dev/null || true
	@git tag -a v$(VERSION) -m 'Tag release version $(VERSION)'
	@echo
	@echo List all tags
	@git tag -l -n --sort=-creatordate
	@echo "== Create tag Succeeded ✅"

push-tag: tag ## Push git tag to remote
	@echo "== Start to push $(PKG_NAME) tag v$(VERSION) to origin"
	@git push origin v$(VERSION)
	@echo "== Push tag Succeeded ✅"

release: clean build check_wheel pypi push-tag ## Release incudes build, pypi, push-tag
	@echo "== Start to make $(PKG_NAME) release"
	@echo "== Release Succeeded ✅"

test: ## Run tests
	@echo "== Start run tests"
	@cd tests && $(PYTHON) -m unittest

coverage: ## Run code coverage
	@echo "== Start run code coverage"
	@cd tests
	@coverage run -m unittest
	@echo "== Report on the results"
	@coverage report -m
	@echo "== get annotated HTML"
	@coverage html  
