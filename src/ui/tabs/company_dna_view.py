"""
Company DNA View Tab
--------------------
Visual profile of the selected company from the 10-year placement archive.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.rag.company_dna import build_company_dna


def render_company_dna_tab(company: str, role: str) -> None:
    st.subheader(f"🧬 {company} — Company DNA & Behavioral Profile")
    st.caption(f"Synthesized from 10 years of placement interviews for **{role}**.")

    try:
        dna = build_company_dna(company, role)
    except Exception as exc:
        st.error(f"Could not load DNA profile for {company}: {exc}")
        return

    # Top Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Selection Rate", f"{dna.selection_rate:.1f}%")
    with m2:
        st.metric("Average Difficulty", f"{dna.avg_difficulty:.2f} / 5.0")
    with m3:
        st.metric("Archive Records Analyzed", f"{dna.total_records:,}")
    with m4:
        top_topic = max(dna.topic_distribution.items(), key=lambda kv: kv[1])[0] if dna.topic_distribution else "DSA"
        st.metric("Primary Evaluation Focus", top_topic)

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        # 1. Topic Distribution
        st.markdown("##### 📌 Topic Weight Distribution")
        topics = list(dna.topic_distribution.keys())
        shares = list(dna.topic_distribution.values())
        fig_topic = px.bar(
            x=topics,
            y=shares,
            labels={"x": "Topic", "y": "Share (%)"},
            color=shares,
            color_continuous_scale="Blues",
            title=f"Core Topics Evaluated at {company}",
        )
        fig_topic.update_layout(showlegend=False, height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_topic, use_container_width=True)

    with col_right:
        # 2. Difficulty Trend Over Years
        st.markdown("##### 📈 10-Year Difficulty Trajectory (2016-2025)")
        years = sorted(dna.difficulty_trend_by_year.keys())
        diffs = [dna.difficulty_trend_by_year[y] for y in years]
        fig_diff = px.line(
            x=years,
            y=diffs,
            markers=True,
            labels={"x": "Year", "y": "Avg Difficulty (1-5)"},
            title="Difficulty Trend Across Placement Seasons",
        )
        fig_diff.update_traces(line_color="#2563EB", marker=dict(size=8, color="#1E40AF"))
        fig_diff.update_layout(yaxis=dict(range=[1, 5]), height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_diff, use_container_width=True)

    st.divider()

    c_rnd, c_rej, c_str = st.columns([1, 1.2, 1.2])

    with c_rnd:
        st.markdown("##### 🔄 Round Structure")
        r_names = list(dna.round_distribution.keys())
        r_shares = list(dna.round_distribution.values())
        fig_round = px.pie(
            names=r_names,
            values=r_shares,
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        fig_round.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_round, use_container_width=True)

    with c_rej:
        st.markdown("##### 🔴 Top Rejection Factors")
        st.caption("Common failure modes noted by company interviewers:")
        for r in dna.top_rejection_tags[:5]:
            pct = round(r["count"] / max(dna.total_records, 1) * 100, 1)
            st.markdown(
                f"""
                <div style="background-color: #FEF2F2; border-left: 3px solid #EF4444; padding: 6px 12px; margin-bottom: 6px; border-radius: 4px;">
                    <span style="font-weight: 600; color: #991B1B;">{r['tag']}</span>
                    <span style="float: right; color: #DC2626; font-size: 0.85rem;">{r['count']} candidates ({pct}%)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c_str:
        st.markdown("##### 🟢 Selected Candidate Strengths")
        st.caption("Distinguishing behaviors of hired candidates:")
        for p in dna.top_positive_tags[:5]:
            pct = round(p["count"] / max(dna.total_records, 1) * 100, 1)
            st.markdown(
                f"""
                <div style="background-color: #F0FDF4; border-left: 3px solid #22C55E; padding: 6px 12px; margin-bottom: 6px; border-radius: 4px;">
                    <span style="font-weight: 600; color: #166534;">{p['tag']}</span>
                    <span style="float: right; color: #15803D; font-size: 0.85rem;">{p['count']} candidates ({pct}%)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # Interviewer Persona and Mindset
    st.markdown("##### 🎯 Interviewer Style & Evaluation Mindset")
    st.info(dna.interviewer_style_summary)
