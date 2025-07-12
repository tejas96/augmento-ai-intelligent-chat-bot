# Makefile for LangGraph Multimodal Chatbot

.PHONY: help install dev build run clean test lint format docker-build docker-run docker-stop deploy

# Default target
help:
	@echo "Available commands:"
	@echo "  install         - Install all dependencies"
	@echo "  install-minimal - Install minimal dependencies (fallback)"
	@echo "  install-safe    - Install with conflict resolution"
	@echo "  fix-install     - Automated installation fix (tries multiple methods)"
	@echo "  test-install    - Test installation and verify imports"
	@echo "  dev             - Run development server"
	@echo "  build           - Build the application"
	@echo "  run             - Run the application"
	@echo "  clean           - Clean temporary files"
	@echo "  test            - Run tests"
	@echo "  lint            - Run linting"
	@echo "  format          - Format code"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-run      - Run Docker container"
	@echo "  docker-stop     - Stop Docker container"
	@echo "  deploy          - Deploy to production"

# Install dependencies
install:
	pip install -r requirements.txt

# Install minimal dependencies (fallback)
install-minimal:
	@echo "Installing minimal dependencies..."
	pip install -r requirements-minimal.txt

# Install dependencies with conflict resolution
install-safe:
	@echo "Installing with conflict resolution..."
	pip install --upgrade pip
	pip install -r requirements.txt --upgrade-strategy eager

# Automated installation fix (tries multiple methods)
fix-install:
	@echo "Running automated installation fix..."
	python fix_installation.py

# Test installation
test-install:
	@echo "Testing installation..."
	python test_installation.py

# Run development server
dev:
	# This command starts the FastAPI app using Uvicorn in development mode.
	# --reload enables auto-reload on code changes.
	# --host 0.0.0.0 makes the server accessible on all network interfaces.
	# --port 8000 sets the port to 8000.
	# --log-level debug enables debug-level logging.
	uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Build the application
build:
	@echo "Building application..."
	python -m compileall .

# Run the application
run:
	uvicorn main:app --host 0.0.0.0 --port 8000

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.log" -delete

# Run tests
test:
	pytest tests/ -v --tb=short

# Run linting
lint:
	ruff check .
	mypy .

# Format code
format:
	black .
	ruff check . --fix

# Docker commands
docker-build:
	docker build -t langgraph-chatbot-backend .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

docker-shell:
	docker-compose exec backend bash

# Development with Docker
docker-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production deployment
deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# AWS deployment helpers
aws-create-bucket:
	aws s3 mb s3://$(S3_BUCKET_NAME) --region $(AWS_REGION)

aws-setup-permissions:
	@echo "Setting up AWS permissions..."
	aws iam create-role --role-name BedrockChatbotRole --assume-role-policy-document file://infrastructure/iam-trust-policy.json
	aws iam attach-role-policy --role-name BedrockChatbotRole --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
	aws iam attach-role-policy --role-name BedrockChatbotRole --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Local development setup
setup-local:
	@echo "Setting up local development environment..."
	pip install -r requirements.txt
	cp .env.example .env
	@echo "Please edit .env file with your AWS credentials"

# Health check
health:
	curl -f http://localhost:8000/health || echo "Service is not running"

# API documentation
docs:
	@echo "API documentation available at: http://localhost:8000/docs"
	@echo "Alternative docs at: http://localhost:8000/redoc"

# Database migrations (future enhancement)
migrate:
	@echo "Running database migrations..."
	# alembic upgrade head

# Backup (future enhancement)
backup:
	@echo "Creating backup..."
	# pg_dump chatbot > backup_$(date +%Y%m%d_%H%M%S).sql

# Load test (future enhancement)
load-test:
	@echo "Running load tests..."
	# locust -f tests/load_test.py --host=http://localhost:8000

# Security scan
security-scan:
	@echo "Running security scans..."
	bandit -r . -x tests/,venv/
	safety check --json

# Performance profiling
profile:
	python -m cProfile -o profile_output.prof main.py
	python -c "import pstats; p = pstats.Stats('profile_output.prof'); p.sort_stats('cumulative').print_stats(20)"

# Generate requirements
freeze:
	pip freeze > requirements_frozen.txt

# Virtual environment setup
venv:
	python -m venv venv
	@echo "Activate with: source venv/bin/activate" 