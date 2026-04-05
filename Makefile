TWINE_REPOSITORY ?= pypi.syslab.com

.PHONY: all
all: .installed.cfg


.venv/bin/buildout: .venv/bin/uv requirements.txt .venv/bin/pre-commit
	# To really be sure we have the desired setuptools we need to uninstall it first
	.venv/bin/uv pip uninstall setuptools
	# ... and reinstall it later
	.venv/bin/uv pip install -r requirements.txt
	.venv/bin/uv pip install horse_with_no_namespace

.venv/bin/pip3:
	python3.11 -m venv .venv

.venv/bin/uv: .venv/bin/pip3
	.venv/bin/pip3 install uv


.PHONY: pre-commit
pre-commit: .venv/bin/pre-commit
.venv/bin/pre-commit: .venv/bin/pip3
	.venv/bin/pip3 install pre-commit
	.venv/bin/pre-commit install



.installed.cfg: .venv/bin/buildout
	./.venv/bin/buildout


.PHONY: check
check: .installed.cfg
	./.venv/bin/pre-commit run --all-files
	./.venv/bin/coverage run ./bin/test -s recensio.plone
	./.venv/bin/coverage report --fail-under=10 -i


.PHONY: clean
clean:
	rm -rf .venv .installed.cfg


# Build custom JavaScript bundle

yarn.lock:
	npx yarn install


.PHONY: bundle
bundle: yarn.lock
	npx yarn build

.PHONY: release
release:
	@echo "Releasing to $(TWINE_REPOSITORY)"
	@echo 'run `make release TWINE_REPOSITORY=<name>` to override'
	TWINE_REPOSITORY=$(TWINE_REPOSITORY) uvx \
	--from zest-releaser \
	--with zest-releaser'[recommended]' \
	--with zestreleaser-towncrier fullrelease
