from __future__ import annotations

import httpx
import streamlit as st
from utils.api import compare_retrieval, get_diagnostics, get_repositories


def main() -> None:
    st.title("Developer Console")
    st.caption(
        "Inspect database metrics, verify API latencies, and "
        "debug RAG retrieval strategies side-by-side."
    )

    # 1. Fetch backend analytics
    try:
        diagnostics = get_diagnostics()
        repos = get_repositories()
    except Exception as exc:
        st.error(f"Failed to fetch system diagnostics: {exc}")
        return

    # 2. Key Metrics Row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Repositories", diagnostics.get("repository_count", 0))
    with c2:
        st.metric("Total Documents", diagnostics.get("document_count", 0))
    with c3:
        st.metric("Total Chunks", diagnostics.get("chunk_count", 0))

    st.markdown("---")

    # 3. Side-by-Side Retrieval Playground
    st.subheader("RAG Retrieval Playground")
    st.caption(
        "Compare semantic (dense), keyword (BM25), and "
        "fused (hybrid) retrieval matching side-by-side."
    )

    if not repos:
        st.info("Ingest a repository to test the retrieval playground.")
    else:
        repo_options = {f"{r['owner']}/{r['name']}": r for r in repos}
        selected_repo_name = st.selectbox("Select Target Repository", list(repo_options.keys()))
        selected_repo = repo_options[selected_repo_name]

        query = st.text_input(
            "Enter Diagnostic Search Query", value="How is database connection handled?"
        )

        if query:
            with st.spinner("Executing retrieval matching across all strategies..."):
                try:
                    comparison = compare_retrieval(query=query, repository_id=selected_repo["id"])

                    col_dense, col_bm25, col_hybrid = st.columns(3)

                    with col_dense:
                        st.markdown("### Dense (Semantic)")
                        hits = comparison.get("dense", [])
                        if not hits:
                            st.write("No matching semantic chunks found.")
                        for hit in hits:
                            with st.container(border=True):
                                if "error" in hit:
                                    st.error(hit["error"])
                                else:
                                    st.markdown(f"**Score:** `{hit['score']:.4f}`")
                                    st.caption(f"Path: `{hit['document_path']}`")
                                    st.code(hit["content"][:300] + "...", language="python")

                    with col_bm25:
                        st.markdown("### BM25 (Keyword)")
                        hits = comparison.get("bm25", [])
                        if not hits:
                            st.write("No keyword matching chunks found.")
                        for hit in hits:
                            with st.container(border=True):
                                if "error" in hit:
                                    st.error(hit["error"])
                                else:
                                    st.markdown(f"**Score:** `{hit['score']:.4f}`")
                                    st.caption(f"Path: `{hit['document_path']}`")
                                    st.code(hit["content"][:300] + "...", language="python")

                    with col_hybrid:
                        st.markdown("### Hybrid (RRF)")
                        hits = comparison.get("hybrid", [])
                        if not hits:
                            st.write("No hybrid results.")
                        for hit in hits:
                            with st.container(border=True):
                                if "error" in hit:
                                    st.error(hit["error"])
                                else:
                                    st.markdown(f"**RRF Score:** `{hit['score']:.6f}`")
                                    st.caption(f"Path: `{hit['document_path']}`")
                                    st.code(hit["content"][:300] + "...", language="python")

                except Exception as exc:
                    st.error(f"Retrieval comparison failed: {exc}")

    st.markdown("---")

    # 4. Service Diagnostics Panel
    st.subheader("Service Latencies & Diagnostics")
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("#### Database & System Metadata")
        for r_det in diagnostics.get("repositories", []):
            st.markdown(
                f"- **{r_det['owner']}/{r_det['name']}**: "
                f"`{r_det['document_count']}` documents, `{r_det['chunk_count']}` chunks"
            )
        if not diagnostics.get("repositories"):
            st.write("No active repository records in database.")

    with c_right:
        st.markdown("#### LLM Provider Ping")
        if st.button("Ping Local Ollama"):
            try:
                # Ping local Ollama server directly from UI client
                resp = httpx.get("http://localhost:11434/", timeout=5.0)
                if resp.status_code == 200:
                    st.success("Ollama connection healthy!")
                    st.json(resp.text)
                else:
                    st.warning(f"Ollama returned status code: {resp.status_code}")
            except Exception as exc:
                st.error(f"Failed to connect to local Ollama server: {exc}")


if __name__ == "__main__":
    main()
