from __future__ import annotations

import streamlit as st
from utils.api import delete_repository, get_repositories, update_repository


def render_repository_cards(repositories: list[dict[str, object]]) -> None:
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

    for repository in repositories:
        repo_id = repository.get("id")
        owner = str(repository.get("owner", "unknown"))
        name = str(repository.get("name", "unknown"))
        status = str(repository.get("status", "unknown")).title()
        docs = int(repository.get("document_count", 0) or 0)
        branch = str(repository.get("default_branch", "-"))
        last_ingested = str(repository.get("last_ingested_at") or "Not ingested")

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {owner}/{name}")
                st.caption(
                    f"**Status:** {status} | **Documents:** {docs} | "
                    f"**Default Branch:** {branch} | **Last Ingested:** {last_ingested}"
                )
            with col2:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                # Check for delete confirmation state
                confirm_key = f"confirm_delete_{repo_id}"
                if st.session_state.get(confirm_key):
                    st.warning("Delete this repo?")
                    yes_btn, no_btn = st.columns(2)
                    with yes_btn:
                        if st.button("Yes", key=f"yes_{repo_id}", type="primary"):
                            try:
                                delete_repository(repo_id)
                                st.success("Deleted!")
                                del st.session_state[confirm_key]
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Failed: {exc}")
                    with no_btn:
                        if st.button("No", key=f"no_{repo_id}"):
                            del st.session_state[confirm_key]
                            st.rerun()
                else:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("Update", key=f"up_btn_{repo_id}", type="primary"):
                            with st.spinner("Updating..."):
                                try:
                                    update_repository(repo_id)
                                    st.success("Updated!")
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"Failed: {exc}")
                    with btn_col2:
                        if st.button("Delete", key=f"del_btn_{repo_id}", type="secondary"):
                            st.session_state[confirm_key] = True
                            st.rerun()


def main() -> None:
    st.title("Repositories")
    st.caption("A quick dashboard of the repositories currently tracked by RepoMind.")

    try:
        repositories = get_repositories()
    except Exception as exc:
        st.error(f"Unable to load repositories: {exc}")
        return

    render_repository_cards(repositories)


if __name__ == "__main__":
    main()
