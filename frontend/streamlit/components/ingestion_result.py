from __future__ import annotations

from typing import Any

import streamlit as st


def render_ingestion_result(payload: dict[str, Any]) -> None:
    repository_name = payload.get("repository", "Unknown repository")
    files_processed = payload.get("files_processed", 0)
    files = payload.get("files", [])

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Repository", repository_name)
    col_b.metric("Files processed", files_processed)
    col_c.metric("File entries", len(files))

    with st.expander("Processed file list", expanded=False):
        if files:
            for item in files:
                path = item.get("path") if isinstance(item, dict) else str(item)
                st.markdown(f"- {path}")
        else:
            st.info("No file paths were returned by the backend for this ingestion job.")

    with st.expander("Raw API response", expanded=False):
        st.json(payload)
