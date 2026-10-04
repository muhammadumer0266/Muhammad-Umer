.PHONY: dev test lint fmt build seed e2e lhci migrate eval loadtest

dev:
	uv run python manage.py migrate
	uv run python manage.py runserver

test:
	DJANGO_SETTINGS_MODULE=config.settings.test uv run pytest --cov --cov-report=term-missing

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run djlint templates --check
	uv run mypy apps config

fmt:
	uv run ruff check --fix .
	uv run ruff format .
	uv run djlint templates --reformat

migrate:
	uv run python manage.py migrate

seed:
	uv run python manage.py import_entries fixtures/sample_entries.json

e2e:
	uv run pytest tests/e2e

lhci:
	npx @lhci/cli autorun

eval:
	uv run python manage.py eval_rag

# Point at a real deployed instance, not the dev server -- see
# tests/perf/locustfile.py's docstring.
loadtest:
	uv run locust -f tests/perf/locustfile.py
