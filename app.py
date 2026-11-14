"""
InterviewDNA — Company-Smart Agentic Mock Interview Coach
=========================================================
Main Streamlit application entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.memory.session_memory import SQLiteSessionStore
from src.orchestrator import Orchestrator
from src.rag.retriever import InterviewRetriever
from src.ui.sidebar import render_sidebar
from src.ui.tabs.coaching_view import render_coaching_tab
from src.ui.tabs.company_dna_view import render_company_dna_tab
from src.ui.tabs.mock_interview import render_mock_interview_tab
from src.ui.tabs.report_view import render_report_tab

# Page Configuration
st.set_page_config(
    page_title="InterviewDNA — Company-Smart Mock Interview Coach",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished look
st.markdown(
    """
    <style>
    /* Clean modern typography and spacing */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    h1, h2, h3 {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        color: #64748B;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.45rem;
        font-weight: 700;
    }
    div[data-baseweb="tab-list"] {
        gap: 1.5rem;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    div[data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
        padding: 0.5rem 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_cached_orchestrator() -> Orchestrator:
    """Initializes and caches the core RAG, agent, and memory orchestrator."""
    retriever = InterviewRetriever()
    sqlite_store = SQLiteSessionStore()
    return Orchestrator(retriever=retriever, sqlite_store=sqlite_store)


def main() -> None:
    orchestrator = get_cached_orchestrator()

    # Render Sidebar and extract parameters
    company, role, pressure_mode, pressure_seconds = render_sidebar(orchestrator)

    # Active Session Memory
    memory = orchestrator.get_or_create_session(
        session_id=st.session_state.session_id,
        sessions_dict=st.session_state.sessions_dict,
        company=company,
        role=role,
    )

    # App Header
    st.markdown('<div class="main-title">InterviewDNA 🧬</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-title">Company-Smart Agentic Mock Interview Coach • '
        f'Targeting <b>{company}</b> ({role})</div>',
        unsafe_allow_html=True,
    )

    # Main 4 Tabs
    tab_interview, tab_dna, tab_coaching, tab_report = st.tabs([
        "🎙️ Mock Interview",
        "🧬 Company DNA",
        "💡 Evidence Coaching",
        "📊 Report & Progress",
    ])

    with tab_interview:
        render_mock_interview_tab(
            orchestrator=orchestrator,
            memory=memory,
            pressure_mode=pressure_mode,
            pressure_seconds=pressure_seconds,
        )

    with tab_dna:
        render_company_dna_tab(company=company, role=role)

    with tab_coaching:
        render_coaching_tab(coach=orchestrator.coach, memory=memory)

    with tab_report:
        render_report_tab(
            report_agent=orchestrator.report_agent,
            memory=memory,
            sqlite_store=orchestrator.sqlite_store,
        )


if __name__ == "__main__":
    main()
