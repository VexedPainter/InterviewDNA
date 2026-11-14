@echo off
REM ============================================================
REM  InterviewDNA — run.bat (Windows equivalent of Makefile)
REM  Usage: run.bat <command>
REM  Commands: setup | ingest | run | test | quality
REM ============================================================

SET CMD=%1

IF "%CMD%"=="setup" GOTO setup
IF "%CMD%"=="ingest" GOTO ingest
IF "%CMD%"=="run" GOTO run
IF "%CMD%"=="test" GOTO test
IF "%CMD%"=="quality" GOTO quality
IF "%CMD%"=="generate" GOTO generate
GOTO usage

:setup
echo [InterviewDNA] Creating virtual environment...
python -m venv venv
echo [InterviewDNA] Installing dependencies...
venv\Scripts\pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt
echo [InterviewDNA] Copying .env.example to .env (edit it with your keys)...
IF NOT EXIST .env copy .env.example .env
echo [InterviewDNA] Setup complete.
GOTO end

:generate
echo [InterviewDNA] Generating synthetic interview archive...
venv\Scripts\python scripts\generate_synthetic_archive.py
GOTO end

:quality
echo [InterviewDNA] Running data quality report...
venv\Scripts\python scripts\data_quality_report.py
GOTO end

:ingest
echo [InterviewDNA] Ingesting archive into ChromaDB...
venv\Scripts\python scripts\ingest_to_chroma.py
GOTO end

:run
echo [InterviewDNA] Starting Streamlit app...
venv\Scripts\streamlit run src\ui\app.py
GOTO end

:test
echo [InterviewDNA] Running test suite...
venv\Scripts\pytest tests\ -v
GOTO end

:usage
echo.
echo Usage: run.bat ^<command^>
echo.
echo   setup     Create venv and install requirements
echo   generate  Generate synthetic interview archive CSV
echo   quality   Print data quality report
echo   ingest    Ingest CSV into ChromaDB vector store
echo   run       Launch Streamlit app
echo   test      Run pytest suite
echo.

:end
