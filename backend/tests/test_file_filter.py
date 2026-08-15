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


def test_allows_docs_directory_files() -> None:
    assert should_ingest_file("docs/guides/first-crew.mdx") is True
    assert should_ingest_file("docs/v1.12.0/en/concepts/tools.mdx") is True


def test_blocks_localized_translation_directories() -> None:
    assert should_ingest_file("docs/v1.12.0/ko/tools/search-research/overview.mdx") is False
    assert should_ingest_file("docs/v1.12.0/pt-BR/tools/search-research/overview.mdx") is False
    assert should_ingest_file("i18n/es/tools/overview.mdx") is False
