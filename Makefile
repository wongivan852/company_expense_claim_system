.PHONY: help install format lint test run clean setup

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

format: ## Format code with black and isort
	black app/ tests/
	isort app/ tests/

lint: ## Run linting checks
	flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503

test: ## Run tests
	pytest tests/ -v

run: ## Start development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

setup: ## Run development setup
	python setup_dev.py

db-init: ## Initialize database with Alembic
	alembic init alembic

db-migrate: ## Create new migration
	alembic revision --autogenerate -m "Auto migration"

db-upgrade: ## Apply migrations
	alembic upgrade head

db-downgrade: ## Rollback last migration
	alembic downgrade -1
