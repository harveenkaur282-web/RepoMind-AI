from backend.app.services.ingestion.file_filter import should_ingest_file


def test_allows_supported_source_file() -> None:
    assert should_ingest_file("backend/app/main.py") is True


def test_allows_markdown_file() -> None:
    assert should_ingest_file("README.md") is True


def test_blocks_node_modules() -> None:
    assert should_ingest_file("node_modules/package/index.js") is False


def test_blocks_git_directory() -> None:
    assert should_ingest_file(".git/config") is False


def test_blocks_env_file() -> None:
    assert should_ingest_file(".env") is False


def test_blocks_unsupported_extension() -> None:
    assert should_ingest_file("assets/logo.png") is False


def test_blocks_large_file() -> None:
    assert should_ingest_file("large.py", file_size=600 * 1024) is False
