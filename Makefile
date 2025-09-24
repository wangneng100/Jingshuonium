.PHONY: help install install-dev test lint format clean run

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev: install  ## Install development dependencies
	pip install -r requirements-dev.txt

test:  ## Run tests
	pytest

lint:  ## Run linting checks
	flake8 src/
	flake8 main.py
	flake8 tests/

format:  ## Format code with black
	black src/
	black main.py
	black tests/

clean:  ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

run:  ## Run the game
	python main.py

build:  ## Build distribution packages
	python setup.py sdist bdist_wheel