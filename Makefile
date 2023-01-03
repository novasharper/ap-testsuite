PIPENV = pipenv
PWD = $(shell pwd)

pipenv:
	$(PIPENV) sync --dev

pylint:
	find $(PWD)/ap_test -name '*.py' -exec \
		$(PIPENV) run pylint --rcfile $(PWD)/pylint.toml \
		{} +

format:
	find $(PWD)/ap_test -name '*.py' -exec \
		$(PIPENV) run black {} +

.PHONY: pipenv pylint
