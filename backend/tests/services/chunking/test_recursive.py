import pytest

from backend.app.services.chunking.recursive import RecursiveChunker


def test_empty_input_returns_no_chunks():
    chunker = RecursiveChunker()

    assert chunker.chunk("") == []


def test_small_document_returns_single_chunk():
    text = "short document"
    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=100, overlap=0)

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)
    assert chunks[0].chunk_index == 0


def test_long_text_is_split_within_chunk_size():
    text = "a" * 250
    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=60, overlap=0)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 60 for chunk in chunks)


def test_chunk_indexes_are_sequential():
    text = "a" * 250
    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=60, overlap=0)

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_overlap_is_applied():
    text = "abcdefghijklmnopqrstuvwxyz" * 5
    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=50, overlap=10)

    assert len(chunks) > 1

    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert current.start_char < previous.end_char


def test_invalid_chunk_size_raises_error():
    chunker = RecursiveChunker()

    with pytest.raises(ValueError):
        chunker.chunk("some text", chunk_size=0)


def test_overlap_cannot_be_negative():
    chunker = RecursiveChunker()

    with pytest.raises(ValueError):
        chunker.chunk("some text", overlap=-1)


def test_overlap_must_be_smaller_than_chunk_size():
    chunker = RecursiveChunker()

    with pytest.raises(ValueError):
        chunker.chunk("some text", chunk_size=50, overlap=50)


def test_paragraph_boundaries_are_preserved_when_possible():
    paragraphs = [
        "First paragraph. " * 4,
        "Second paragraph. " * 4,
        "Third paragraph. " * 4,
    ]
    text = "\n\n".join(paragraphs)

    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=100, overlap=0)

    assert len(chunks) == 3
    assert chunks[0].text == paragraphs[0]
    assert chunks[1].text == paragraphs[1]
    assert chunks[2].text == paragraphs[2]


def test_very_long_text_is_split_without_empty_chunks():
    text = "W" * 310
    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=100, overlap=0)

    assert all(chunk.text for chunk in chunks)
    assert all(len(chunk.text) <= 100 for chunk in chunks)


def test_chunk_offsets_match_original_text():
    text = (
        "First paragraph with some content.\n\n"
        "Second paragraph with more content.\n\n"
        "Third paragraph with additional content."
    )
    chunker = RecursiveChunker()

    chunks = chunker.chunk(text, chunk_size=45, overlap=0)

    for chunk in chunks:
        assert text[chunk.start_char : chunk.end_char] == chunk.text
