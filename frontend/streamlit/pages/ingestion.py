from __future__ import annotations

from urllib.parse import urlparse

import streamlit as st
from components.ingestion_result import render_ingestion_result
from utils.api import ingest_repository


def parse_repository_url(raw_url: str) -> tuple[str, str]:
    value = raw_url.strip()
    if not value:
        raise ValueError("Please enter a GitHub repository URL.")

    if "/" not in value:
        raise ValueError(
            "Enter a valid GitHub repository URL like https://github.com/owner/repository"
        )

    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"

    parsed = urlparse(value)
    netloc = (parsed.netloc or parsed.path).lower()
    if netloc and netloc not in {"github.com", "www.github.com"}:
        raise ValueError("Only GitHub repository URLs are supported.")

    path_parts = [part for part in (parsed.path or "/").split("/") if part and part != ".git"]
    if len(path_parts) < 2:
        raise ValueError("The URL must include both the owner and repository name.")

    owner = path_parts[0]
    repo = path_parts[1]
    if not owner or not repo:
        raise ValueError("The owner and repository name could not be parsed from the URL.")

    return owner, repo


def main() -> None:
    st.title("Ingest a GitHub Repository")
    st.caption(
        "The current RepoMind workflow is request/response based: "
        "validate the URL, submit to the backend, and render the "
        "actual ingestion response."
    )

    raw_url = st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repository",
        help="Use the full repository URL, for example https://github.com/microsoft/vscode",
    )

    submitted = st.button("Ingest repository", type="primary")
    if not submitted:
        return

    try:
        owner, repo = parse_repository_url(raw_url)
    except ValueError as exc:
        st.error(str(exc))
        return

    try:
        with st.spinner("Sending repository request to the FastAPI backend..."):
            result = ingest_repository(owner=owner, repo=repo)
    except Exception as exc:
        st.error(f"Ingestion failed: {exc}")
        return

    st.success("Repository ingestion completed.")
    render_ingestion_result(result)


if __name__ == "__main__":
    main()
