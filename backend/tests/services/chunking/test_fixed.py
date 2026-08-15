import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path.cwd()))

from backend.app.services.chunking.fixed import FixedSizeChunker


def test_empty_text_returns_no_chunks():
    chunker = FixedSizeChunker()
    chunks = chunker.chunk("")
    assert chunks == []


def test_text_smaller_than_chunk_size_produces_single_chunk():
    text = "short text"
    chunker = FixedSizeChunker()
    chunks = chunker.chunk(text, chunk_size=100, overlap=0)
    assert len(chunks) == 1

    ch = chunks[0]
    assert ch.text == text
    assert ch.start_char == 0
    assert ch.end_char == len(text)
    assert ch.chunk_index == 0


def test_normal_splitting_without_overlap():
    text = "a" * 25
    chunker = FixedSizeChunker()
    chunks = chunker.chunk(text, chunk_size=10, overlap=0)

    assert [len(ch.text) for ch in chunks] == [10, 10, 5]
    assert [ch.chunk_index for ch in chunks] == [0, 1, 2]

    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 10
    assert chunks[1].start_char == 10
    assert chunks[1].end_char == 20
    assert chunks[2].start_char == 20
    assert chunks[2].end_char == 25


def test_overlap_produces_expected_starts_and_ends():
    text = "x" * 30
    chunker = FixedSizeChunker()
    chunks = chunker.chunk(text, chunk_size=10, overlap=3)

    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 10

    assert chunks[1].start_char == 7
    assert chunks[1].end_char == 17

    assert chunks[2].start_char == 14

    assert chunks[-1].end_char == min(len(text), chunks[-1].start_char + 10)

    assert [ch.chunk_index for ch in chunks] == list(range(len(chunks)))


@pytest.mark.parametrize("invalid_chunk_size", [0, -1])
def test_invalid_chunk_size_raises_value_error(invalid_chunk_size):
    chunker = FixedSizeChunker()
    with pytest.raises(ValueError):
        chunker.chunk("some text", chunk_size=invalid_chunk_size)


@pytest.mark.parametrize("invalid_overlap", [-5])
def test_negative_overlap_raises_value_error(invalid_overlap):
    chunker = FixedSizeChunker()
    with pytest.raises(ValueError):
        chunker.chunk("some text", overlap=invalid_overlap)


def test_overlap_greater_or_equal_chunk_size_raises():
    chunker = FixedSizeChunker()
    with pytest.raises(ValueError):
        chunker.chunk("some text", chunk_size=5, overlap=5)

    with pytest.raises(ValueError):
        chunker.chunk("some text", chunk_size=5, overlap=6)
