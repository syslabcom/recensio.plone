.PHONY: all
all: .installed.cfg


py3/bin/buildout: py3/bin/pip3 py3/bin/pre-commit
	./py3/bin/pip3 uninstall -y setuptools
	./py3/bin/pip3 install -IUr https://dist.plone.org/release/6-latest/requirements.txt


.PHONY: pre-commit
pre-commit: py3/bin/pre-commit
py3/bin/pre-commit: py3/bin/pip3
	./py3/bin/pip3 install pre-commit
	./py3/bin/pre-commit install


py3/bin/pip3:
	python3 -m venv py3


.installed.cfg: py3/bin/buildout
	./py3/bin/buildout


.PHONY: check
check: .installed.cfg
	./py3/bin/pre-commit run --all-files
	./bin/coverage run ./bin/test -s recensio.plone
	./bin/coverage report --fail-under=10 -i


.PHONY: clean
clean:
	rm -rf ./py3


# Build custom JavaScript bundle

yarn.lock:
	npx yarn install


.PHONY: bundle
bundle: yarn.lock
	npx yarn build
