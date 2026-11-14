@echo off
REM ============================================================
REM  InterviewDNA — run.bat (Windows equivalent of Makefile)
REM  Usage: run.bat <command>
REM  Commands: dev | api | frontend | setup | ingest | generate | quality | doctor | test
REM ============================================================

SET CMD=%1

IF "%CMD%"=="dev" GOTO dev
IF "%CMD%"=="api" GOTO api
IF "%CMD%"=="frontend" GOTO frontend
IF "%CMD%"=="setup" GOTO setup
IF "%CMD%"=="generate" GOTO generate
IF "%CMD%"=="quality" GOTO quality
IF "%CMD%"=="ingest" GOTO ingest
IF "%CMD%"=="doctor" GOTO doctor
IF "%CMD%"=="test" GOTO test
IF "%CMD%"=="run" GOTO run
GOTO usage

:dev
echo [InterviewDNA] Starting FastAPI backend (:8000) and Vite frontend (:5173)...
cd frontend
call npx concurrently -n "API,VITE" -c "cyan.bold,magenta.bold" "..\venv\Scripts\python -m uvicorn src.api.main:app --app-dir .. --reload --port 8000" "npm run dev"
cd ..
GOTO end

:api
echo [InterviewDNA] Starting FastAPI backend on http://localhost:8000...
venv\Scripts\python -m uvicorn src.api.main:app --reload --port 8000
GOTO end

:frontend
echo [InterviewDNA] Starting Vite frontend on http://localhost:5173...
cd frontend
call npm run dev
cd ..
GOTO end

:doctor
echo [InterviewDNA] Checking system health & dependencies...
venv\Scripts\python scripts\doctor.py
GOTO end

:setup
echo [InterviewDNA] Creating virtual environment...
python -m venv venv
echo [InterviewDNA] Installing Python dependencies...
venv\Scripts\pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt
echo [InterviewDNA] Installing Frontend dependencies...
cd frontend
call npm install
cd ..
echo [InterviewDNA] Copying .env.example to .env (if not present)...
IF NOT EXIST .env copy .env.example .env
IF NOT EXIST frontend\.env copy frontend\.env.example frontend\.env
echo [InterviewDNA] Setup complete! Run 'run.bat dev' to start.
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
echo [InterviewDNA] Starting legacy Streamlit UI...
venv\Scripts\streamlit run src\ui\app.py
GOTO end

:test
echo [InterviewDNA] Running test suite...
venv\Scripts\pytest tests\ -v
GOTO end

:usage
echo.
echo ============================================================
echo   InterviewDNA - Fast Launcher
echo ============================================================
echo   run.bat dev       Start BOTH Backend (:8000) and Frontend (:5173) together
echo   run.bat api       Start FastAPI Backend only (:8000)
echo   run.bat frontend  Start Vite React Frontend only (:5173)
echo   run.bat doctor    Check environment, ports, and configuration
echo   run.bat setup     Install Python + Node dependencies
echo   run.bat ingest    Ingest CSV into ChromaDB vector store
echo   run.bat test      Run pytest suite
echo.
echo Defaulting to 'run.bat dev'...
echo.
GOTO dev

:end
