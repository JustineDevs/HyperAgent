# Makefile for HyperAgent Docker operations

.PHONY: help build up down logs restart clean test

# Default target
help:
	@echo "HyperAgent Docker Commands:"
	@echo "  make build          - Build Docker image"
	@echo "  make up             - Start all services (development)"
	@echo "  make up-prod        - Start all services (production)"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs"
	@echo "  make restart        - Restart services"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make test           - Run tests in container"
	@echo "  make shell          - Open shell in container"
	@echo "  make migrate        - Run database migrations"

# Build Docker image
build:
	@echo "[*] Building HyperAgent Docker image..."
	docker build -t hyperagent:latest .

# Start development stack
up:
	@echo "[*] Starting HyperAgent development stack..."
	docker-compose up -d
	@echo "[+] Services started. Use 'make logs' to view logs."

# Start production stack
up-prod:
	@echo "[*] Starting HyperAgent production stack..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "[+] Production services started."

# Stop all services
down:
	@echo "[*] Stopping HyperAgent services..."
	docker-compose down

# View logs
logs:
	docker-compose logs -f hyperagent

# Restart services
restart:
	@echo "[*] Restarting HyperAgent services..."
	docker-compose restart

# Clean up containers and volumes
clean:
	@echo "[!] Removing containers and volumes..."
	docker-compose down -v
	@echo "[+] Cleanup complete."

# Run tests in container
test:
	@echo "[*] Running tests in container..."
	docker-compose exec hyperagent pytest tests/ -v

# Open shell in container
shell:
	docker-compose exec hyperagent /bin/bash

# Run database migrations
migrate:
	@echo "[*] Running database migrations..."
	docker-compose exec hyperagent alembic upgrade head

# Health check
health:
	@echo "[*] Checking service health..."
	@docker-compose ps
	@curl -f http://localhost:8000/api/v1/health/basic || echo "[-] API not responding"

