#!/usr/bin/env bash
# ============================================================
#  InterviewDNA — run.sh
#  Usage: ./run.sh <command>
#  Commands: setup | generate | quality | ingest | run | test
# ============================================================

set -e

CMD=$1

case "$CMD" in
  setup)
    echo "[InterviewDNA] Creating virtual environment..."
    python3 -m venv venv
    echo "[InterviewDNA] Installing dependencies..."
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt
    if [ ! -f .env ]; then
      cp .env.example .env
      echo "[InterviewDNA] Copied .env.example to .env"
    fi
    echo "[InterviewDNA] Setup complete."
    ;;
  generate)
    echo "[InterviewDNA] Generating synthetic interview archive..."
    venv/bin/python scripts/generate_synthetic_archive.py
    ;;
  quality)
    echo "[InterviewDNA] Running data quality report..."
    venv/bin/python scripts/data_quality_report.py
    ;;
  ingest)
    echo "[InterviewDNA] Ingesting archive into ChromaDB..."
    venv/bin/python scripts/ingest_to_chroma.py
    ;;
  run)
    echo "[InterviewDNA] Starting Streamlit app..."
    venv/bin/streamlit run src/ui/app.py
    ;;
  test)
    echo "[InterviewDNA] Running test suite..."
    venv/bin/pytest tests/ -v
    ;;
  *)
    echo "Usage: ./run.sh {setup|generate|quality|ingest|run|test}"
    exit 1
    ;;
esac
