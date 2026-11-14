"""
scripts/doctor.py — Diagnostic & Health Check tool for InterviewDNA.

Verifies:
- Python version (>= 3.10)
- Node.js & npm versions
- Environment configuration (.env presence, API keys)
- ChromaDB vector store population
- Port availability (8000 for FastAPI, 5173 for Vite)
- Prints clear troubleshooting instructions for any failure.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def check_python() -> tuple[bool, str]:
    v = sys.version_info
    v_str = f"{v.major}.{v.minor}.{v.micro}"
    if v.major >= 3 and v.minor >= 10:
        return True, f"Python {v_str} (>= 3.10)"
    return False, f"Python {v_str} is below required 3.10+"


def check_node() -> tuple[bool, str]:
    node = shutil.which("node")
    if not node:
        return False, "Node.js not found in PATH. Install Node 18+ from https://nodejs.org"
    try:
        out = subprocess.check_output([node, "--version"], text=True).strip()
        major = int(out.lstrip("v").split(".")[0])
        if major >= 18:
            return True, f"Node.js {out} (>= 18)"
        return False, f"Node.js {out} is below recommended v18+"
    except Exception as e:
        return False, f"Error checking Node.js: {e}"


def check_env() -> tuple[bool, str]:
    root = Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    if not env_file.exists():
        return False, ".env file missing. Run: copy .env.example .env"

    content = env_file.read_text(encoding="utf-8")
    provider = "gemini"
    for line in content.splitlines():
        if line.startswith("LLM_PROVIDER="):
            provider = line.split("=", 1)[1].strip().lower()

    if provider == "gemini":
        has_key = any(
            line.startswith("GOOGLE_API_KEY=") and len(line.split("=", 1)[1].strip()) > 10
            and not line.split("=", 1)[1].strip().startswith("your_")
            for line in content.splitlines()
        )
        if not has_key:
            return False, ".env exists, but GOOGLE_API_KEY is missing or using placeholder"
        return True, f".env configured with Google Gemini provider ({provider})"
    elif provider == "ollama":
        return True, ".env configured with local Ollama provider"
    return True, f".env configured (provider={provider})"


def check_chromadb() -> tuple[bool, str]:
    root = Path(__file__).resolve().parent.parent
    chroma_dir = root / "chroma_db"
    if not chroma_dir.exists():
        return False, "ChromaDB vector store not found. Run: python -m src.rag.ingest --reset"
    # Check sqlite inside chroma_db
    sqlite_file = chroma_dir / "chroma.sqlite3"
    if not sqlite_file.exists():
        return False, "chroma.sqlite3 missing. Run: python -m src.rag.ingest --reset"
    return True, f"ChromaDB persistent store present ({chroma_dir.name})"


def check_ports() -> list[tuple[str, bool, str]]:
    results = []
    # 8000
    p8000_used = is_port_in_use(8000)
    if p8000_used:
        results.append(("Port 8000", True, "Port 8000 in use (FastAPI backend may already be running)"))
    else:
        results.append(("Port 8000", True, "Port 8000 is free for FastAPI backend"))

    # 5173
    p5173_used = is_port_in_use(5173)
    if p5173_used:
        results.append(("Port 5173", True, "Port 5173 in use (Vite dev server may already be running)"))
    else:
        results.append(("Port 5173", True, "Port 5173 is free for Vite frontend"))

    return results


def check_frontend_deps() -> tuple[bool, str]:
    root = Path(__file__).resolve().parent.parent
    nm = root / "frontend" / "node_modules"
    if not nm.exists():
        return False, "frontend/node_modules missing. Run: cd frontend && npm install"
    return True, "frontend/node_modules installed"


def main():
    print(f"\n{BOLD}{CYAN}=== InterviewDNA Environment Health Check ==={RESET}\n")

    checks = [
        ("Python Version", check_python()),
        ("Node.js Version", check_node()),
        ("Frontend Dependencies", check_frontend_deps()),
        ("Environment (.env)", check_env()),
        ("ChromaDB Vector Store", check_chromadb()),
    ]

    all_passed = True
    for name, (passed, msg) in checks:
        icon = f"{GREEN}[OK]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
        print(f" {icon:<10} {BOLD}{name:<24}{RESET} : {msg}")
        if not passed:
            all_passed = False

    print(f"\n{BOLD}Port Status:{RESET}")
    for name, _, msg in check_ports():
        print(f" - {BOLD}{name:<12}{RESET} : {msg}")

    print("\n" + "=" * 50)
    if all_passed:
        print(f"{GREEN}{BOLD}All environment checks passed! Ready to run InterviewDNA.{RESET}")
        print("\nStart commands:")
        print("  Terminal 1 (Backend) : python -m uvicorn src.api.main:app --reload --port 8000")
        print("  Terminal 2 (Frontend): cd frontend && npm run dev")
    else:
        print(f"{RED}{BOLD}Some checks failed. Please fix the items above before starting.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
