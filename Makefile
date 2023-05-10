.PHONY: all
all: .installed.cfg


py/bin/buildout: py/bin/pip3 py/bin/pre-commit
	./py/bin/pip3 uninstall -y setuptools
	./py/bin/pip3 install -IUr https://dist.plone.org/release/6-latest/requirements.txt


pre-commit: py/bin/pre-commit
py/bin/pre-commit: py/bin/pip3
	./py/bin/pip3 install pre-commit
	./py/bin/pre-commit install


py/bin/pip3:
	python3 -m venv py


.installed.cfg: py/bin/buildout
	./py/bin/buildout


.PHONY: check
check: .installed.cfg
	./py/bin/pre-commit run --all-files
	./bin/coverage run ./bin/test -s recensio.plone
	./bin/coverage report --fail-under=10 -i


.PHONY: clean
clean:
	rm -rf ./py


# Build custom JavaScript bundle

yarn.lock:
	npx yarn install


.PHONY: bundle
bundle: yarn.lock
	npx yarn build
