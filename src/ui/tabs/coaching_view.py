"""
Coaching View Tab
-----------------
Evidence-grounded coaching advice citing real archive record IDs with expandable snippets.
"""

from __future__ import annotations

import streamlit as st

from src.agents.coach import CoachAgent
from src.memory.session_memory import SessionMemory
from src.ui.helpers import get_record_by_id


def render_coaching_tab(coach: CoachAgent, memory: SessionMemory) -> None:
    st.subheader("💡 Evidence-Grounded Coaching")
    st.caption(
        f"Personalized coaching grounded in historical feedback patterns for "
        f"**{memory.state.company}** ({memory.state.role})."
    )

    # Custom Coaching Query Box
    c_query, c_btn = st.columns([4, 1])
    with c_query:
        user_query = st.text_input(
            "Ask Coach about a specific topic, concept, or company practice:",
            value="",
            placeholder="e.g. How does Zoho evaluate DSA recursion? Or: Tips for Amazon Leadership Principles",
        )
    with c_btn:
        st.write("")
        st.write("")
        ask_clicked = st.button("Get Coaching", use_container_width=True)

    if ask_clicked and user_query.strip():
        with st.spinner("Retrieving historical precedents and formulating coaching advice..."):
            advice = coach.run(memory, query=user_query.strip())
            st.session_state["latest_coaching_advice"] = advice

    # Display Coaching Advice (either latest or auto-generated)
    advice = st.session_state.get("latest_coaching_advice")
    if not advice:
        # Generate initial default coaching on first view
        with st.spinner("Synthesizing company interview advice..."):
            advice = coach.run(memory, query=f"Tips and preparation strategy for {memory.state.company}")
            st.session_state["latest_coaching_advice"] = advice

    if advice:
        st.markdown(
            f"""
            <div style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 12px 16px; border-radius: 6px; margin-bottom: 1rem;">
                <h4 style="margin: 0 0 6px 0; color: #1E40AF;">📋 Strategic Summary</h4>
                <p style="margin: 0; color: #1E3A8A; font-size: 0.95rem;">{advice.summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if advice.no_evidence_notice:
            st.warning(f"⚠️ {advice.no_evidence_notice}")

        st.markdown("#### 🎯 Targeted Actionable Tips")
        for idx, tip in enumerate(advice.tips, 1):
            with st.container():
                st.markdown(f"**Tip {idx}:** {tip.text}")

                # Citation Chips
                if tip.evidence_ids:
                    chips_html = '<div style="margin-top: 4px; margin-bottom: 8px;">'
                    for eid in tip.evidence_ids:
                        yr = f", {tip.evidence_year}" if tip.evidence_year else ""
                        chips_html += (
                            f'<span style="display: inline-block; background-color: #E2E8F0; color: #334155; '
                            f'padding: 2px 8px; border-radius: 12px; font-size: 0.78rem; font-weight: 600; margin-right: 6px;">'
                            f'🏷️ {eid}{yr}</span>'
                        )
                    chips_html += '</div>'
                    st.markdown(chips_html, unsafe_allow_html=True)

                    # Expandable Real Historical Feedback Snippets
                    with st.expander(f"🔍 Inspect Archive Evidence for Tip {idx} ({len(tip.evidence_ids)} records)"):
                        for eid in tip.evidence_ids:
                            rec = get_record_by_id(eid)
                            if rec:
                                outcome_color = "#166534" if rec.get("outcome") == "Selected" else "#991B1B"
                                st.markdown(
                                    f"""
                                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                                        <div style="font-size: 0.82rem; font-weight: 600; color: #64748B; margin-bottom: 4px;">
                                            Record: <span style="color: #0F172A;">{rec.get('record_id')}</span> |
                                            Year: <span style="color: #0F172A;">{rec.get('year')}</span> |
                                            Round: <span style="color: #0F172A;">{rec.get('round_type')}</span> |
                                            Outcome: <span style="color: {outcome_color}; font-weight: bold;">{rec.get('outcome')}</span> (Score: {rec.get('score_given')}/10)
                                        </div>
                                        <div style="font-size: 0.9rem; color: #1E293B; margin-bottom: 4px;">
                                            <b>Interviewer Feedback:</b> <i>"{rec.get('feedback_text')}"</i>
                                        </div>
                                        <div style="font-size: 0.8rem; color: #64748B;">
                                            <b>Tags:</b> {rec.get('feedback_tags')}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.caption(f"Record {eid} loaded from vector metadata.")
                st.write("")
