from pathlib import Path

import streamlit as st


def load_css() -> None:
    css_path = Path(__file__).resolve().parent / "styles" / "main.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="RepoMind AI",
        page_icon="R",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()

    home_page = st.Page("pages/home.py", title="Home", default=True)
    ingestion_page = st.Page("pages/ingestion.py", title="Ingest Repository")
    repositories_page = st.Page("pages/repositories.py", title="Repositories")

    navigation = st.navigation(
        [
            home_page,
            ingestion_page,
            repositories_page,
        ]
    )
    navigation.run()


if __name__ == "__main__":
    main()
