"""
Report & Progress Tab
---------------------
Visual scorecard, benchmark comparison, radar chart, 7-day plan,
Markdown/PDF downloads, and cross-session progress history from SQLite.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.agents.report import REPORTS_DIR, ReportAgent
from src.memory.session_memory import SessionMemory, SQLiteSessionStore


def render_report_tab(
    report_agent: ReportAgent,
    memory: SessionMemory,
    sqlite_store: SQLiteSessionStore,
) -> None:
    st.subheader("📊 Session Report & Placement Readiness")
    st.caption(f"Session ID: `{memory.state.session_id}` | Company: **{memory.state.company}** ({memory.state.role})")

    # Generate or Retrieve Session Report
    if "current_session_report" not in st.session_state:
        if memory.state.history:
            with st.spinner("Compiling full session report and benchmark analytics..."):
                rep = report_agent.run(memory)
                st.session_state["current_session_report"] = rep
        else:
            rep = None
    else:
        rep = st.session_state["current_session_report"]

    # Re-run report button if new turns were completed
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("🔄 Refresh Report", use_container_width=True):
            with st.spinner("Recomputing scorecard..."):
                rep = report_agent.run(memory)
                st.session_state["current_session_report"] = rep
                st.rerun()

    if not rep or not rep.turn_scores:
        st.info("ℹ️ No turns evaluated in this session yet. Complete at least one interview turn in the **Mock Interview** tab to view your performance report.")
        _render_cross_session_history(sqlite_store, memory.user_nickname)
        return

    # Top KPI Metrics & Verdict
    st.divider()
    k1, k2, k3, k4, k5 = st.columns(5)

    verdict_colors = {
        "Selected Ready": "#166534",
        "Borderline": "#B45309",
        "Needs Practice": "#991B1B",
    }
    v_color = verdict_colors.get(rep.verdict, "#1E293B")

    with k1:
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 600;">VERDICT</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: {v_color}; margin-top: 4px;">{rep.verdict}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.metric("Overall Score", f"{rep.averages.get('overall', 0):.1f} / 10", delta=rep.trend.capitalize())
    with k3:
        st.metric("Correctness", f"{rep.averages.get('correctness', 0):.1f} / 10")
    with k4:
        st.metric("Depth", f"{rep.averages.get('depth', 0):.1f} / 10")
    with k5:
        st.metric("Communication", f"{rep.averages.get('communication', 0):.1f} / 10")

    st.divider()

    # Visualizations: Radar Chart & Benchmark Comparison
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### 🕸️ Skills Competency Radar")
        categories = ["Correctness", "Depth", "Communication", "Overall"]
        values = [
            rep.averages.get("correctness", 0),
            rep.averages.get("depth", 0),
            rep.averages.get("communication", 0),
            rep.averages.get("overall", 0),
        ]
        # Close radar loop
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name='Your Session',
            line_color='#2563EB',
            fillcolor='rgba(37, 99, 235, 0.25)',
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            height=320,
            margin=dict(l=40, r=40, t=20, b=20),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_chart2:
        st.markdown("##### 🏛️ Benchmark vs Historical Selected Candidates")
        if rep.benchmark_comparison:
            bc = rep.benchmark_comparison
            bench_val = bc.get("avg_score_selected", 7.8)
            cand_val = rep.averages.get("overall", 0)

            fig_bench = go.Figure(data=[
                go.Bar(name='Your Average', x=['Overall Score'], y=[cand_val], marker_color='#3B82F6', text=[f"{cand_val:.1f}"], textposition='auto'),
                go.Bar(name=f"{memory.state.company} Hired Avg", x=['Overall Score'], y=[bench_val], marker_color='#10B981', text=[f"{bench_val:.1f}"], textposition='auto'),
            ])
            fig_bench.update_layout(
                barmode='group',
                yaxis=dict(range=[0, 10]),
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_bench, use_container_width=True)
            st.caption(f"Benchmark based on **{bc.get('sample_size', 0)}** selected candidates at {memory.state.company}.")
        else:
            st.info("Benchmark data loading from archive...")

    st.divider()

    # Strengths, Gaps, and 7-Day Roadmap
    c_str, c_gap = st.columns(2)
    with c_str:
        st.markdown("##### ✅ Proven Strengths")
        if rep.top_strengths:
            for s in rep.top_strengths:
                st.markdown(f"- 🟢 **{s}**")
        else:
            st.caption("None recorded.")

    with c_gap:
        st.markdown("##### ⚠️ Key Priority Gaps")
        if rep.top_gaps:
            for g in rep.top_gaps:
                st.markdown(f"- 🔴 **{g}**")
        else:
            st.caption("No critical gaps detected.")

    st.markdown("##### 📅 7-Day Targeted Improvement Roadmap")
    for item in rep.improvement_plan:
        st.markdown(f"- 📌 {item}")

    st.divider()

    # Download Buttons (Markdown & PDF)
    st.markdown("##### 📥 Export Placement Readiness Report")
    md_file = REPORTS_DIR / f"{rep.session_id}.md"
    pdf_file = REPORTS_DIR / f"{rep.session_id}.pdf"

    d1, d2 = st.columns(2)
    with d1:
        if md_file.exists():
            with open(md_file, encoding="utf-8") as f:
                st.download_button(
                    label="📥 Download Markdown Summary (.md)",
                    data=f.read(),
                    file_name=f"InterviewDNA_{memory.state.company}_{rep.session_id}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
    with d2:
        if pdf_file.exists():
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📄 Download Official PDF Scorecard (.pdf)",
                    data=f.read(),
                    file_name=f"InterviewDNA_{memory.state.company}_{rep.session_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    st.divider()
    _render_cross_session_history(sqlite_store, memory.user_nickname)


def _render_cross_session_history(sqlite_store: SQLiteSessionStore, nickname: str) -> None:
    """Renders progress line chart across past sessions stored in SQLite."""
    st.markdown(f"##### 📈 Performance Progression Across Sessions for '{nickname}'")
    try:
        sessions = sqlite_store.get_user_sessions(nickname)
        if len(sessions) < 1:
            st.caption("Complete more mock interview sessions to unlock cross-session trend tracking.")
            return

        # Fetch turns for each session to get average scores
        chart_data = []
        for s in reversed(sessions):
            turns = sqlite_store.get_session_turns(s["session_id"])
            if turns:
                scored = [t.evaluation.overall for t in turns if t.evaluation and t.evaluation.overall > 0]
                if scored:
                    avg_score = sum(scored) / len(scored)
                    chart_data.append({
                        "Session": s["session_id"][:8],
                        "Company": s["company"],
                        "Average Score": round(avg_score, 1),
                        "Date": s.get("created_at", "")[:10],
                    })

        if chart_data:
            df_hist = pd.DataFrame(chart_data)
            fig_hist = px.line(
                df_hist,
                x="Session",
                y="Average Score",
                color="Company",
                markers=True,
                title="Score Progression Across Mock Interviews",
            )
            fig_hist.update_layout(yaxis=dict(range=[0, 10]), height=280)
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.caption("No completed evaluation turns found in past sessions.")
    except Exception as e:
        st.caption(f"Could not load cross-session progress: {e}")
