.PHONY: all
all: .installed.cfg

py3/bin/buildout: py3/bin/pip3 requirements.txt
	./py3/bin/pip3 uninstall -y setuptools
	./py3/bin/pip3 install -IUr requirements.txt
	./py3/bin/pre-commit install

py3/bin/pip3:
	python3 -m venv py3

.installed.cfg: py3/bin/buildout
	./py3/bin/buildout -c dev.cfg

.PHONY: check
check:
	./py3/bin/pre-commit run --all-files
	./bin/coverage run ./bin/test -s recensio.plone
	./bin/coverage report --fail-under=60 -i

.PHONY: clean
clean:
	rm -rf ./py3
