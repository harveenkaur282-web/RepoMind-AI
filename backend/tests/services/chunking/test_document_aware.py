from backend.app.services.chunking.document_aware import DocumentAwareChunker


def test_empty_input_returns_no_chunks():
    chunker = DocumentAwareChunker()

    assert chunker.chunk("") == []


def test_markdown_is_split_at_headings():
    text = (
        "# Overview\n"
        "This is the overview.\n\n"
        "## Architecture\n"
        "This describes the architecture.\n\n"
        "## Installation\n"
        "These are the installation steps."
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        path="README.md",
        chunk_size=500,
    )

    assert len(chunks) == 3
    assert chunks[0].metadata["document_type"] == "markdown"
    assert chunks[0].metadata["heading"] == "Overview"
    assert chunks[1].metadata["heading"] == "Architecture"
    assert chunks[2].metadata["heading"] == "Installation"


def test_markdown_code_block_heading_is_not_treated_as_document_heading():
    text = (
        "# Example\n\n"
        "```python\n"
        "# This is a comment, not a Markdown heading\n"
        "def hello():\n"
        "    return 'hello'\n"
        "```\n"
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        path="README.md",
        chunk_size=500,
    )

    assert len(chunks) == 1
    assert "def hello()" in chunks[0].text
    assert chunks[0].metadata["heading"] == "Example"


def test_code_is_split_at_top_level_symbols():
    text = (
        "import os\n\n"
        "class UserService:\n"
        "    def login(self):\n"
        "        return True\n\n"
        "def health_check():\n"
        "    return 'ok'\n"
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        path="services/user.py",
        chunk_size=500,
    )

    assert len(chunks) >= 2

    symbols = [chunk.metadata.get("symbol") for chunk in chunks]

    assert "UserService" in symbols
    assert "health_check" in symbols


def test_oversized_code_block_is_still_split():
    text = "def large_function():\n" + ("    value = 'something'\n" * 20)

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        path="large.py",
        chunk_size=100,
    )

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 100 for chunk in chunks)


def test_issue_content_is_chunked_as_structured_content():
    text = (
        "# Problem\n"
        "Authentication fails for some users.\n\n"
        "# Expected behavior\n"
        "Users should be able to log in normally.\n\n"
        "# Additional context\n"
        "The problem started after the latest deployment."
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        document_type="issue",
        path="issues/42",
        chunk_size=500,
    )

    assert len(chunks) == 3
    assert all(chunk.metadata["document_type"] == "issue" for chunk in chunks)


def test_pull_request_content_is_chunked_as_structured_content():
    text = (
        "# Summary\n"
        "Added repository ingestion.\n\n"
        "# Changes\n"
        "Added the ingestion service and database persistence.\n\n"
        "# Testing\n"
        "Added unit tests."
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        document_type="pull_request",
        chunk_size=500,
    )

    assert len(chunks) == 3
    assert all(chunk.metadata["document_type"] == "pull_request" for chunk in chunks)


def test_release_content_is_chunked_as_structured_content():
    text = (
        "# Features\n"
        "Added repository ingestion.\n\n"
        "# Bug fixes\n"
        "Fixed duplicate repository handling.\n\n"
        "# Improvements\n"
        "Improved ingestion performance."
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        document_type="release",
        chunk_size=500,
    )

    assert len(chunks) == 3
    assert all(chunk.metadata["document_type"] == "release" for chunk in chunks)


def test_generic_text_falls_back_to_paragraph_chunking():
    text = "First paragraph with useful information.\n\nSecond paragraph with more information."

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        document_type="text",
        path="notes.txt",
        chunk_size=500,
    )

    assert len(chunks) == 2
    assert all(chunk.metadata["document_type"] == "text" for chunk in chunks)


def test_chunk_indexes_are_sequential():
    text = "# One\nFirst section.\n\n# Two\nSecond section.\n\n# Three\nThird section."

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        path="README.md",
        chunk_size=500,
    )

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_chunk_offsets_point_to_original_text():
    text = (
        "# Introduction\n"
        "This is the introduction.\n\n"
        "## Architecture\n"
        "This explains the architecture."
    )

    chunker = DocumentAwareChunker()

    chunks = chunker.chunk(
        text,
        path="README.md",
        chunk_size=500,
    )

    for chunk in chunks:
        assert text[chunk.start_char : chunk.end_char] == chunk.text
