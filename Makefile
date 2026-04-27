PWD = $(shell pwd)

install:
	poetry install --with dev

pylint:
	find $(PWD)/ap_test -name '*.py' -exec \
		poetry run pylint --rcfile $(PWD)/pylint.toml {} +

format:
	find $(PWD)/ap_test -name '*.py' -exec \
		poetry run black {} +

.PHONY: install pylint format
