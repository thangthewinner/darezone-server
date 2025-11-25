.PHONY: run dev test format lint clean help

help:
	@echo "DareZone Backend Commands:"
	@echo "  make run      - Run server (production mode)"
	@echo "  make dev      - Run server with auto-reload (development)"
	@echo "  make test     - Run tests"
	@echo "  make format   - Format code with black"
	@echo "  make lint     - Lint code with flake8"
	@echo "  make clean    - Clean cache files"

run:
	uv run python main.py

dev:
	uv run python main.py

test:
	.venv/bin/pytest

format:
	.venv/bin/black app tests

lint:
	.venv/bin/flake8 app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
