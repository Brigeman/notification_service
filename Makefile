.PHONY: help install install-dev migrate runserver celery test lint format check pre-commit-install clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make migrate          - Run database migrations"
	@echo "  make runserver        - Run Django development server"
	@echo "  make celery           - Run Celery worker"
	@echo "  make test             - Run tests"
	@echo "  make test-coverage    - Run tests with HTML coverage report"
	@echo "  make test-coverage-term - Run tests with terminal coverage report"
	@echo "  make lint             - Run linters (ruff, mypy)"
	@echo "  make format           - Format code (black, isort)"
	@echo "  make check            - Run all checks (lint + format check)"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make clean            - Clean cache files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

migrate:
	python manage.py migrate

runserver:
	python manage.py runserver

celery:
	celery -A notification_service worker -l info

test:
	pytest

test-coverage:
	pytest --cov=notifications --cov-report=html --cov-report=term-missing

test-coverage-term:
	pytest --cov=notifications --cov-report=term-missing

lint:
	ruff check .
	mypy .

format:
	black .
	isort .

check:
	black --check .
	isort --check .
	ruff check .
	mypy .

pre-commit-install:
	pre-commit install

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
