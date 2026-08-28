import sys
from pathlib import Path

# Ensure frontend directory is in sys.path for relative component/util imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    assistant_page = st.Page("pages/assistant.py", title="AI Assistant")

    st.sidebar.title("Settings")
    dev_mode = st.sidebar.toggle("Developer Mode", value=False)

    pages = [home_page, ingestion_page, repositories_page, assistant_page]
    if dev_mode:
        developer_page = st.Page("pages/developer.py", title="Developer Console")
        pages.append(developer_page)

    navigation = st.navigation(pages)
    navigation.run()


if __name__ == "__main__":
    main()
