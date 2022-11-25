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
PKG_NAME = atlassian_api_py
VERSION ?= $(shell ls dist/atlassian_api_py* | cut -d - -f 2)
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

install: ## Install deps for development
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	pre-commit install

check_wheel:
	@ls dist/$(PKG_NAME)-$(VERSION)-py3-none-any.whl

check_branch:
ifneq ($(BRANCH),master)
	@echo "Please release from master branch. exit."
	@exit 1
endif

build: clean ## Make wheel package
	@$(PYTHON) -m pip wheel -w dist --no-deps .

install-whl: build ## Install wheel package
	@$(PIP) install dist/$(PKG_NAME)-$(VERSION)-py3-none-any.whl

clean: ## Cleanup generate files
	@rm -rf dist build $(PKG_NAME)*

pypi: build ## Upload to offical pypi
	@echo "== Start to upload $(PKG_NAME) to https://pypi.org/"
	@rm ~/.pypirc 2>/dev/null || true
	@twine upload dist/*

test-pypi: build ## Upload to test-pypi
	@echo "== Start to upload $(PKG_NAME) to https://test.pypi.org/"
	@twine upload --repository testpypi dist/*

tag: ## Create git tag on local
	@echo "== Start to make $(PKG_NAME) tag v$(VERSION)"
	@git tag -d v$(VERSION) 2>/dev/null || true
	@git tag -a v$(VERSION) -m 'Tag release version $(VERSION)'
	@echo
	@echo List all tags
	@git tag -l -n --sort=-creatordate

push-tag: tag ## Push git tag to remote
	@echo "== Start to push $(PKG_NAME) tag v$(VERSION) to origin"
	@git push origin v$(VERSION)

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

mypy: ## Check typing
	mypy atlassian

release: clean build check_wheel check_branch pypi push-tag ## Release incudes build, pypi, push-tag
