.PHONY:

build: install

install:
	pipenv install --dev

serve:
	pipenv run heroku local

run:
	DEBUG=True pipenv run python app/app.py