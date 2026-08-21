from __future__ import annotations

import streamlit as st
from utils.api import get_repositories, query_rag, submit_feedback


def main() -> None:
    st.title("AI Assistant")
    st.caption(
        "Ask questions about your ingested codebase repositories using "
        "dense, sparse, or hybrid retrieval."
    )

    # 1. Fetch available repositories
    try:
        repos = get_repositories()
    except Exception as exc:
        st.error(f"Failed to load repositories: {exc}")
        return

    if not repos:
        st.info("No repositories have been ingested yet. Please ingest a repository first.")
        st.page_link("pages/ingestion.py", label="Go to Ingestion page →")
        return

    # 2. Sidebar options
    st.sidebar.title("Configuration")

    # Create selectbox options
    repo_options = {f"{r['owner']}/{r['name']}": r for r in repos}
    selected_repo_name = st.sidebar.selectbox("Select Repository", list(repo_options.keys()))
    selected_repo = repo_options[selected_repo_name]

    strategy = st.sidebar.selectbox(
        "Retrieval Strategy",
        ["dense", "bm25", "hybrid"],
        index=0,  # default to dense (most reliable)
        help=(
            "dense uses semantic vector similarity, bm25 uses text keyword matches, "
            "hybrid uses reciprocal rank fusion."
        ),
    )

    # 3. Chat Session Initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = {}

    # Clear chat when switching repository
    if (
        "current_repo" not in st.session_state
        or st.session_state.current_repo != selected_repo["id"]
    ):
        st.session_state.current_repo = selected_repo["id"]
        st.session_state.messages = []
        st.session_state.feedback_submitted = {}

    # Clear chat history button
    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.feedback_submitted = {}
        st.rerun()

    # 4. Render message history
    for idx_msg, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("chunks"):
                with st.expander("Show Retrieved Source Chunks"):
                    for idx, chunk in enumerate(msg["chunks"]):
                        st.markdown(f"**Source {idx + 1}:** `{chunk['document_path']}`")
                        st.code(chunk["content"], language="python")

            # Feedback UI for completed assistant responses
            if msg["role"] == "assistant" and msg.get("request_id"):
                req_id = msg["request_id"]
                if req_id in st.session_state.feedback_submitted:
                    st.success("Feedback recorded.")
                else:
                    col1, col2, _ = st.columns([1, 1, 6])
                    with col1:
                        if st.button("Helpful", key=f"up_{req_id}_{idx_msg}"):
                            try:
                                submit_feedback(req_id, "positive")
                                st.session_state.feedback_submitted[req_id] = "positive"
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
                    with col2:
                        if st.button("Not helpful", key=f"down_{req_id}_{idx_msg}"):
                            st.session_state.feedback_submitted[req_id] = "pending_negative"
                            st.rerun()

                    if st.session_state.feedback_submitted.get(req_id) == "pending_negative":
                        with st.form(key=f"feedback_form_{req_id}"):
                            comment = st.text_area("Tell us more (optional):", key=f"text_{req_id}")
                            submit_comment = st.form_submit_button("Submit")
                            if submit_comment:
                                try:
                                    submit_feedback(req_id, "negative", comment)
                                    st.session_state.feedback_submitted[req_id] = "negative"
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")

    # 5. User Input and API Query
    user_query = st.chat_input("Ask a question about the repository...")

    if user_query:
        # Display user query
        with st.chat_message("user"):
            st.markdown(user_query)

        st.session_state.messages.append({"role": "user", "content": user_query})

        # Display assistant response placeholder and query API
        with st.chat_message("assistant"):
            with st.spinner("Retrieving context and generating answer..."):
                try:
                    result = query_rag(
                        query=user_query,
                        strategy=strategy,
                        repository_id=selected_repo["id"],
                    )
                    answer = result["answer"]
                    chunks = result.get("chunks", [])
                    request_id = result.get("request_id")

                    st.markdown(answer)

                    # Display retrieved source chunks
                    if chunks:
                        with st.expander("Show Retrieved Source Chunks"):
                            for idx, chunk in enumerate(chunks):
                                st.markdown(f"**Source {idx + 1}:** `{chunk['document_path']}`")
                                st.code(chunk["content"], language="python")

                    # Save to state
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "chunks": chunks,
                            "request_id": request_id,
                        }
                    )
                    st.rerun()

                except Exception as exc:
                    st.error(f"Error querying assistant: {exc}")


if __name__ == "__main__":
    main()
