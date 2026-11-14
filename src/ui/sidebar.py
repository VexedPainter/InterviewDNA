"""
Sidebar Module
--------------
Renders session controls, company/role configuration, mode selectors,
pressure mode toggle, and New Session management.
"""

from __future__ import annotations

import uuid

import streamlit as st

from src.memory.session_memory import SessionMemory
from src.orchestrator import Orchestrator

COMPANIES = [
    "Zoho",
    "Amazon",
    "Google",
    "TCS",
    "Infosys",
    "Accenture",
    "Deloitte",
    "Flipkart",
]

COMPANY_ROLES: dict[str, list[str]] = {
    "Zoho": ["Software Developer", "Member Technical Staff", "UI Developer", "DevOps Engineer"],
    "Amazon": ["SDE-I", "SDE-II", "Business Analyst", "Data Engineer", "Solutions Architect"],
    "Google": ["Software Engineer", "SWE-II", "Site Reliability Engineer", "Data Scientist"],
    "TCS": ["Software Engineer", "Data Analyst", "Systems Engineer", "Business Analyst"],
    "Infosys": ["Systems Engineer", "Technology Analyst", "Digital Specialist", "Process Executive"],
    "Accenture": ["Associate Software Engineer", "Analyst", "Cloud Engineer", "Packaged App Developer"],
    "Deloitte": ["Technology Analyst", "Analyst", "Consultant", "Risk Advisory Analyst"],
    "Flipkart": ["SDE-I", "SDE-II", "Data Engineer", "Platform Engineer", "Product Analyst"],
}

ROUNDS = [
    "Aptitude",
    "Technical",
    "Managerial",
    "HR",
]


def render_sidebar(orchestrator: Orchestrator) -> tuple[str, str, bool, int]:
    """
    Renders sidebar controls and returns (company, role, pressure_mode, pressure_seconds).
    """
    with st.sidebar:
        st.markdown("## 🧬 InterviewDNA")
        st.caption("Company-Smart Agentic Mock Interview Coach")

        # Nickname
        nickname = st.text_input("Candidate Name", value="Student", key="sidebar_nickname")

        # Company & Dynamic Role Selectors
        company = st.selectbox("Target Company", COMPANIES, index=0, key="sidebar_company")
        available_roles = COMPANY_ROLES.get(company, ["Software Engineer"])
        role = st.selectbox("Target Role", available_roles, index=0, key="sidebar_role")

        st.divider()

        # Round Mode
        round_mode = st.radio(
            "Round Mode",
            ["Full Loop (All Rounds)", "Single Round Focus"],
            index=0,
            key="sidebar_round_mode",
        )
        selected_single_round = None
        if round_mode == "Single Round Focus":
            selected_single_round = st.selectbox("Select Target Round", ROUNDS, index=1, key="sidebar_single_round")

        # Difficulty Mode
        diff_mode = st.radio(
            "Difficulty Progression",
            ["Adaptive (Dynamic)", "Fixed Level"],
            index=0,
            key="sidebar_diff_mode",
        )
        fixed_difficulty = 3
        if diff_mode == "Fixed Level":
            fixed_difficulty = st.slider("Fixed Difficulty", min_value=1, max_value=5, value=3, key="sidebar_fixed_diff")

        st.divider()

        # Pressure Mode Toggle
        pressure_mode = st.toggle("⏱️ Pressure Mode", value=False, help="Adds a timed countdown to answer each question.")
        pressure_seconds = 120
        if pressure_mode:
            pressure_seconds = st.select_slider(
                "Time Limit Per Question",
                options=[60, 90, 120, 180],
                value=120,
                format_func=lambda s: f"{s} seconds",
                key="sidebar_pressure_time",
            )

        # Sync with Session Memory
        if "session_id" not in st.session_state:
            st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"

        if "sessions_dict" not in st.session_state:
            st.session_state.sessions_dict = {}

        memory: SessionMemory = orchestrator.get_or_create_session(
            session_id=st.session_state.session_id,
            sessions_dict=st.session_state.sessions_dict,
            company=company,
            role=role,
            user_nickname=nickname,
        )

        # Apply settings
        memory.state.company = company
        memory.state.role = role
        memory.user_nickname = nickname
        if selected_single_round:
            memory.state.round_type = selected_single_round
        if diff_mode == "Fixed Level":
            memory.state.difficulty_level = fixed_difficulty

        st.divider()

        # Session Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Round", memory.state.round_type)
        with col2:
            st.metric("Difficulty", f"Level {memory.state.difficulty_level}/5")

        st.write("")
        if st.button("🔄 New Session", use_container_width=True, type="secondary"):
            new_id = f"sess_{uuid.uuid4().hex[:8]}"
            st.session_state.session_id = new_id
            if new_id in st.session_state.sessions_dict:
                del st.session_state.sessions_dict[new_id]
            st.session_state.pop("latest_coaching_advice", None)
            st.session_state.pop("current_session_report", None)
            st.session_state.pop("latest_trace", None)
            st.session_state.pop("question_start_time", None)
            st.rerun()

        return company, role, pressure_mode, pressure_seconds
