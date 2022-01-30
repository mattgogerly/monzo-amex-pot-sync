install:
	@pipenv install --dev

run:
	@pipenv run python main.py

lint:
	@pipenv run flake8

.PHONY: install run lint