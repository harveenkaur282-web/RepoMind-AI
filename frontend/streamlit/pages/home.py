from __future__ import annotations

import streamlit as st

from components.status_badge import render_status_badge
from utils.api import get_health


def render_health_summary() -> None:
    try:
        health = get_health()
    except Exception as exc:
        st.warning(f"Health check unavailable: {exc}")
        return

    if not health:
        st.warning("The backend did not return health data.")
        return

    status = str(health.get("status", "unknown")).lower()
    service = str(health.get("service", "RepoMind API"))
    version = str(health.get("version", "unknown"))

    st.markdown(
        f"""
        <div class="health-card">
            <div class="health-header">
                <span class="health-label">API Health</span>
                <span class="status-pill {status}">{status.title()}</span>
            </div>
            <div class="health-meta">
                <div>
                    <span>Service</span>
                    <strong>{service}</strong>
                </div>
                <div>
                    <span>Version</span>
                    <strong>{version}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.title("RepoMind AI")
    st.caption("Repository ingestion and persistence for GitHub codebases.")

    render_status_badge("Current stage: Repository Ingestion", "warning")

    st.markdown(
        """
        RepoMind AI ingests a GitHub repository, filters the files that matter, and stores the repository and document metadata in PostgreSQL.
        """
    )

    st.page_link("pages/ingestion.py", label="Go to repository ingestion →")
    st.page_link("pages/repositories.py", label="Open repository dashboard →")

    render_health_summary()


if __name__ == "__main__":
    main()
