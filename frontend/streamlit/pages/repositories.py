from __future__ import annotations

import pandas as pd
import streamlit as st
from utils.api import get_repositories


def normalize_repository_row(repository: dict[str, object]) -> dict[str, object]:
    status = str(repository.get("status", "unknown")).title()
    return {
        "Owner": str(repository.get("owner", "unknown")),
        "Repository": str(repository.get("name", "unknown")),
        "Status": status,
        "Docs": int(repository.get("document_count", 0) or 0),
        "Branch": str(repository.get("default_branch", "-")),
        "Last ingested": str(repository.get("last_ingested_at") or "Not ingested"),
    }


def render_repository_table(repositories: list[dict[str, object]]) -> None:
    if not repositories:
        st.info("No repositories have been ingested yet. Use the ingestion page to add one.")
        st.markdown(
            """
            <div class="empty-state">
                <h4>No repository records available</h4>
                <p>The backend has no ingested repositories to display yet.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    rows = [normalize_repository_row(repository) for repository in repositories]
    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Owner": st.column_config.TextColumn("Owner"),
            "Repository": st.column_config.TextColumn("Repository"),
            "Status": st.column_config.TextColumn("Status"),
            "Docs": st.column_config.NumberColumn("Docs"),
            "Branch": st.column_config.TextColumn("Branch"),
            "Last ingested": st.column_config.TextColumn("Last ingested"),
        },
    )


def main() -> None:
    st.title("Repositories")
    st.caption("A quick dashboard of the repositories currently tracked by RepoMind.")

    try:
        repositories = get_repositories()
    except Exception as exc:
        st.error(f"Unable to load repositories: {exc}")
        return

    render_repository_table(repositories)


if __name__ == "__main__":
    main()
