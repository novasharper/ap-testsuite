PIPENV = pipenv
PWD = $(shell pwd)

pipenv:
	PIPENV_VERBOSITY=-1 \
	$(PIPENV) sync --dev

pylint:
	PIPENV_VERBOSITY=-1 \
	find $(PWD)/ap_test -name '*.py' -exec \
		$(PIPENV) run pylint --rcfile $(PWD)/pylint.toml {} +

format:
	PIPENV_VERBOSITY=-1 \
	find $(PWD)/ap_test -name '*.py' -exec \
		$(PIPENV) run black {} +

.PHONY: pipenv pylint
