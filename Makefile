.PHONY: help setup test clean lint format install run-api run-dashboard

# Variables
PYTHON := python3
PIP := pip3
PROJECT_NAME := rgm-analytics

# Default target
help:
	@echo "RGM Analytics Platform - Available commands:"
	@echo "  make setup          - Initial project setup"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean temporary files"
	@echo "  make run-api       - Run FastAPI server"
	@echo "  make run-dashboard - Run Streamlit dashboard"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker services"

# Setup project
setup:
	$(PYTHON) -m venv venv
	. venv/bin/activate && $(PIP) install --upgrade pip
	. venv/bin/activate && $(PIP) install -r requirements.txt
	. venv/bin/activate && pre-commit install
	cp .env.example .env
	@echo "✅ Setup complete! Don't forget to activate venv: source venv/bin/activate"

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html

# Lint code
lint:
	flake8 src/ tests/
	mypy src/
	black --check src/ tests/
	isort --check-only src/ tests/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Run API
run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run Dashboard
run-dashboard:
	streamlit run dashboards/streamlit/app.py

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database commands
db-init:
	$(PYTHON) scripts/setup_database.py

db-migrate:
	alembic upgrade head

db-seed:
	$(PYTHON) scripts/generate_sample_data.py

# Generate synthetic data
generate-data:
	$(PYTHON) scripts/generate_sample_data.py --records 100000

# Run daily pipeline
run-pipeline:
	$(PYTHON) scripts/run_daily_pipeline.py --date today