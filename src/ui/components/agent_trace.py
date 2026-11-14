"""
Agent Trace component for visualizing real-time agentic routing and retrieval.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_agent_trace(trace: dict[str, Any] | None) -> None:
    """Renders a collapsible or inline trace card showing agentic execution details."""
    if not trace:
        return

    with st.expander("🧭 Live Agent Execution Trace", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Active Agent", trace.get("routed_agent", "Router"))
        with c2:
            conf = trace.get("confidence", 1.0)
            st.metric("Intent Confidence", f"{int(conf * 100)}%")
        with c3:
            st.metric("Fallback Level", trace.get("fallback_level", "Direct (Exact)"))
        with c4:
            st.metric("RAG Records Retrieved", str(trace.get("records_retrieved", 0)))

        st.caption(f"**Intent Detection:** {trace.get('intent', 'PRACTICE')} | **Path:** {'⚡ Fast-Path Pattern' if trace.get('fast_path') else '🧠 LCEL Semantic Classifier'}")
        if trace.get("reasoning"):
            st.caption(f"**Reasoning:** {trace.get('reasoning')}")
