from __future__ import annotations

import streamlit as st


def render_status_badge(label: str, tone: str = "neutral") -> None:
    tone_map = {
        "neutral": "status-badge neutral",
        "success": "status-badge success",
        "warning": "status-badge warning",
        "danger": "status-badge danger",
    }
    css_class = tone_map.get(tone, tone_map["neutral"])
    st.markdown(f'<div class="{css_class}">{label}</div>', unsafe_allow_html=True)
