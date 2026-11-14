"""
Mock Interview Tab
------------------
Interactive turn-by-turn interview simulation with real-time rubric evaluations,
pressure mode countdown timer, STAR structure checks, and adaptive follow-ups.
"""

from __future__ import annotations

import time

import streamlit as st

from src.memory.session_memory import SessionMemory
from src.orchestrator import Orchestrator
from src.schemas.models import EvaluationResult, TurnRecord
from src.ui.components.agent_trace import render_agent_trace


def render_mock_interview_tab(
    orchestrator: Orchestrator,
    memory: SessionMemory,
    pressure_mode: bool = False,
    pressure_seconds: int = 120,
) -> None:
    st.subheader(f"🎙️ Mock Interview — {memory.state.company}")
    st.caption(f"Role: **{memory.state.role}** | Round: **{memory.state.round_type}** | Adaptive Difficulty: **Level {memory.state.difficulty_level}/5**")

    # If no question is active yet, offer to start
    if not memory.has_pending_question and not memory.state.history:
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 10px; padding: 30px; text-align: center; margin: 20px 0;">
                <h3 style="color: #0F172A; margin-bottom: 8px;">Ready to begin your mock round?</h3>
                <p style="color: #64748B; max-width: 500px; margin: 0 auto 20px auto;">
                    You will be interviewed with historical questions asked by <b>{memory.state.company}</b> interviewers.
                    Your answers will be calibrated in real-time against real rubric standards.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c_start, _ = st.columns([1, 3])
        with c_start:
            if st.button("🚀 Start First Question", type="primary", use_container_width=True):
                with st.spinner("Retrieving first question from company question bank..."):
                    turn = orchestrator.interviewer.run(memory)
                    st.session_state["latest_trace"] = {
                        "routed_agent": "Interviewer Agent",
                        "intent": "PRACTICE",
                        "confidence": 0.99,
                        "fallback_level": "company_role",
                        "records_retrieved": 5,
                        "fast_path": True,
                        "reasoning": "Interview initialization",
                    }
                    if pressure_mode:
                        st.session_state["question_start_time"] = time.time()
                    st.rerun()
        return

    # Render Completed Turns & Historical Evaluation Cards
    completed_turns = [t for t in memory.state.history if t.evaluation is not None]
    for turn in completed_turns:
        _render_turn_card(turn)

    # Render Current Active Question (if pending answer)
    if memory.has_pending_question:
        active_turn = memory.get_active_turn()
        _render_active_question_input(
            orchestrator=orchestrator,
            memory=memory,
            active_turn=active_turn,
            pressure_mode=pressure_mode,
            pressure_seconds=pressure_seconds,
        )
    else:
        # No pending question; provide Next Question or End Interview buttons
        c_next, c_end, _ = st.columns([1, 1, 2])
        with c_next:
            if st.button("➡️ Next Question", type="primary", use_container_width=True):
                with st.spinner("Fetching next question..."):
                    turn = orchestrator.interviewer.run(memory)
                    st.session_state["latest_trace"] = {
                        "routed_agent": "Interviewer Agent",
                        "intent": "PRACTICE",
                        "confidence": 0.98,
                        "fallback_level": "company_role",
                        "records_retrieved": 5,
                        "fast_path": True,
                    }
                    if pressure_mode:
                        st.session_state["question_start_time"] = time.time()
                    st.rerun()
        with c_end:
            if st.button("🏁 End Interview Round", use_container_width=True):
                with st.spinner("Generating placement report..."):
                    rep = orchestrator.report_agent.run(memory)
                    st.session_state["current_session_report"] = rep
                    st.success("Round completed! View your full scorecard in the **Report & Progress** tab.")

    # Render Live Agent Trace
    st.divider()
    render_agent_trace(st.session_state.get("latest_trace"))


def _render_turn_card(turn: TurnRecord) -> None:
    """Renders a past completed turn with question, answer, and evaluation card."""
    with st.container():
        fu_badge = " [Follow-up Probe]" if turn.is_followup else ""
        st.markdown(
            f"""
            <div style="background-color: #F1F5F9; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;">
                <div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase;">
                    Turn #{turn.turn_number} • {turn.round_type or 'Technical'} Round • {turn.topic or 'General'}{fu_badge}
                </div>
                <div style="font-size: 1.05rem; font-weight: 600; color: #0F172A; margin: 4px 0 8px 0;">
                    {turn.question}
                </div>
                <div style="font-size: 0.92rem; color: #334155; background: white; padding: 8px 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
                    <b>Your Answer:</b> {turn.candidate_answer}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ev: EvaluationResult | None = turn.evaluation
        if ev:
            with st.expander(f"📊 Evaluation Scorecard — Overall: {ev.overall:.1f}/10", expanded=False):
                # 3 Score Gauges
                g1, g2, g3 = st.columns(3)
                with g1:
                    st.write(f"**Correctness:** {ev.correctness:.1f}/10")
                    st.progress(ev.correctness / 10.0)
                with g2:
                    st.write(f"**Depth & Edge Cases:** {ev.depth:.1f}/10")
                    st.progress(ev.depth / 10.0)
                with g3:
                    st.write(f"**Communication:** {ev.communication:.1f}/10")
                    st.progress(ev.communication / 10.0)

                st.write("")
                col_m, col_w = st.columns(2)
                with col_m:
                    st.markdown("**✅ Covered Points:**")
                    if ev.matched_points:
                        for p in ev.matched_points:
                            st.markdown(f"- 🟢 {p}")
                    else:
                        st.caption("None clearly covered.")

                with col_w:
                    st.markdown("**⚠️ Missed / Weak Points:**")
                    if ev.missed_points:
                        for p in ev.missed_points:
                            st.markdown(f"- 🟡 {p}")
                    if ev.red_flags:
                        for rf in ev.red_flags:
                            st.markdown(f"- 🔴 **Flag:** {rf}")
                    if not ev.missed_points and not ev.red_flags:
                        st.caption("No significant omissions.")

                # Behavioral STAR Check indicator
                if (turn.topic or "").lower() == "behavioral":
                    star_detected = any("STAR" in p for p in ev.matched_points)
                    if star_detected:
                        st.success("🌟 STAR Structure Detected: Clear Situation, Task, Action, and Result demonstrated.")
                    else:
                        st.warning("⚠️ STAR Structure Incomplete: Remember to clearly delineate Situation, Task, Action, and quantifiable Result.")

        st.write("")


def _render_active_question_input(
    orchestrator: Orchestrator,
    memory: SessionMemory,
    active_turn: TurnRecord,
    pressure_mode: bool,
    pressure_seconds: int,
) -> None:
    """Renders the active prompt, timer, answer text area, and submission trigger."""
    fu_tag = " [Follow-up Probe]" if active_turn.is_followup else ""

    # Pressure Mode Countdown
    if pressure_mode:
        start_time = st.session_state.get("question_start_time", time.time())
        elapsed = int(time.time() - start_time)
        remaining = max(0, pressure_seconds - elapsed)
        bar_pct = max(0.0, min(1.0, remaining / pressure_seconds))

        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.progress(bar_pct)
        with col_t2:
            timer_color = "red" if remaining < 20 else "black"
            st.markdown(f"⏱️ **Pressure Timer:** <span style='color:{timer_color}; font-weight:bold;'>{remaining}s remaining</span>", unsafe_allow_html=True)

    # Active Question Box
    st.markdown(
        f"""
        <div style="background-color: #EFF6FF; border-left: 5px solid #2563EB; border-radius: 8px; padding: 16px 20px; margin: 10px 0 16px 0;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #1E40AF; text-transform: uppercase;">
                Question #{active_turn.turn_number} • {active_turn.round_type or 'Technical'} Round • {active_turn.topic or 'General'}{fu_tag}
            </div>
            <div style="font-size: 1.15rem; font-weight: 600; color: #1E3A8A; margin-top: 6px;">
                {active_turn.question}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Optional Voice Input (st.audio_input)
    audio_val = None
    if hasattr(st, "audio_input"):
        with st.expander("🎙️ Optional Voice Input (Speech-to-Text)"):
            audio_val = st.audio_input("Record your answer verbally:")
            if audio_val:
                st.info("Audio recorded successfully. You can transcribe or complement your answer in the text area below.")

    # Answer Text Area
    user_answer = st.text_area(
        "Your Answer:",
        value="",
        placeholder="Structure your answer clearly. For technical questions, mention trade-offs and complexity. For behavioral, follow STAR...",
        height=140,
        key=f"answer_input_{active_turn.turn_number}",
    )

    c_submit, c_hint = st.columns([1, 3])
    with c_submit:
        submitted = st.button("Submit Answer", type="primary", use_container_width=True)

    # Edge cases & submission handling
    if submitted:
        cleaned_ans = user_answer.strip()
        if not cleaned_ans and not audio_val:
            st.error("⚠️ Please enter an answer before submitting.")
            return

        if len(cleaned_ans.split()) < 4:
            st.warning("⚠️ Your answer appears very brief (< 4 words). Detailed answers allow the evaluator to accurately score depth and correctness.")

        with st.spinner("Evaluator Agent calibrating your response against rubric..."):
            ans_to_evaluate = cleaned_ans if cleaned_ans else "Candidate provided verbal response via audio."
            eval_res = orchestrator.evaluator.run(
                candidate_answer=ans_to_evaluate,
                turn=active_turn,
                memory=memory,
            )

            st.session_state["latest_trace"] = {
                "routed_agent": "Evaluator Agent",
                "intent": "EVALUATE",
                "confidence": 0.98,
                "fallback_level": "company_role",
                "records_retrieved": 0,
                "fast_path": True,
            }

            # Check if adaptive follow-up is warranted
            if eval_res.needs_followup and memory.state.followup_count < 1:
                with st.spinner("Interviewer Agent preparing targeted follow-up probe..."):
                    orchestrator.interviewer.generate_followup(memory, eval_res)
                    if pressure_mode:
                        st.session_state["question_start_time"] = time.time()

            st.rerun()
