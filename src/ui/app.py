"""
Streamlit entry point redirecting to main app.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import app

if __name__ == "__main__":
    app.main()
