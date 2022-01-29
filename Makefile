install:
	@pipenv install --dev

run:
	@pipenv run python monzo-amex-pot/main.py

lint:
	@pipenv run flake8

.PHONY: install run lint