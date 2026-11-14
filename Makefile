# ============================================================
#  InterviewDNA — Makefile
#  Usage: make <command>
#  Commands: setup | generate | quality | ingest | run | test
# ============================================================

.PHONY: setup generate quality ingest run test help

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
STREAMLIT = $(VENV)/bin/streamlit
PYTEST = $(VENV)/bin/pytest

# Windows compatibility fallback
ifeq ($(OS),Windows_NT)
    PYTHON = $(VENV)/Scripts/python.exe
    PIP = $(VENV)/Scripts/pip.exe
    STREAMLIT = $(VENV)/Scripts/streamlit.exe
    PYTEST = $(VENV)/Scripts/pytest.exe
endif

help:
	@echo "Available commands:"
	@echo "  make setup     Create virtual environment and install dependencies"
	@echo "  make generate  Generate synthetic interview archive CSV"
	@echo "  make quality   Run data quality report"
	@echo "  make ingest    Ingest CSV into ChromaDB vector store"
	@echo "  make run       Launch Streamlit UI"
	@echo "  make test      Run pytest suite"

setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

generate:
	$(PYTHON) scripts/generate_synthetic_archive.py

quality:
	$(PYTHON) scripts/data_quality_report.py

ingest:
	$(PYTHON) scripts/ingest_to_chroma.py

run:
	$(STREAMLIT) run src/ui/app.py

api:
	$(PYTHON) -m uvicorn src.api.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	cd frontend && npx concurrently -n "API,VITE" -c "cyan.bold,magenta.bold" "python -m uvicorn src.api.main:app --app-dir .. --reload --port 8000" "npm run dev"

test:
	$(PYTEST) tests/ -v
