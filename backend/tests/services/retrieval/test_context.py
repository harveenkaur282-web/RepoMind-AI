
from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.services.retrieval.context import ContextAssembler
from backend.app.services.retrieval.service import RetrievalResult


def test_assemble_preserves_order_and_formats_correctly() -> None:
    doc1 = Document(path="app/main.py")
    chunk1 = Chunk(id=1, content="print('hello')", document=doc1)

    doc2 = Document(path="app/utils.py")
    chunk2 = Chunk(id=2, content="def add(a, b): return a + b", document=doc2)

    results = [
        RetrievalResult(chunk=chunk1, score=0.9),
        RetrievalResult(chunk=chunk2, score=0.8),
    ]

    assembler = ContextAssembler()
    assembled = assembler.assemble(results)

    assert assembled.total_chunks == 2
    assert len(assembled.chunks) == 2
    assert assembled.chunks[0] is chunk1
    assert assembled.chunks[1] is chunk2

    expected_str = (
        "---\nDocument: app/main.py\nContent:\nprint('hello')\n"
        "---\nDocument: app/utils.py\nContent:\ndef add(a, b): return a + b\n"
    )
    assert assembled.context_str == expected_str
    assert assembled.total_tokens == len(expected_str) // 4


def test_assemble_removes_duplicates() -> None:
    doc = Document(path="app/main.py")
    chunk1 = Chunk(id=1, content="first appearance", document=doc)
    chunk2 = Chunk(id=2, content="unique chunk", document=doc)
    chunk1_duplicate = Chunk(id=1, content="duplicate block", document=doc)

    results = [
        RetrievalResult(chunk=chunk1, score=0.95),
        RetrievalResult(chunk=chunk2, score=0.85),
        RetrievalResult(chunk=chunk1_duplicate, score=0.75),
    ]

    assembler = ContextAssembler()
    assembled = assembler.assemble(results)

    # Should only contain chunk1 and chunk2, in that order
    assert assembled.total_chunks == 2
    assert assembled.chunks[0] is chunk1
    assert assembled.chunks[1] is chunk2


def test_assemble_respects_max_chunks() -> None:
    chunk1 = Chunk(id=1, content="chunk1")
    chunk2 = Chunk(id=2, content="chunk2")

    results = [
        RetrievalResult(chunk=chunk1, score=0.9),
        RetrievalResult(chunk=chunk2, score=0.8),
    ]

    assembler = ContextAssembler(max_chunks=1)
    assembled = assembler.assemble(results)

    assert assembled.total_chunks == 1
    assert assembled.chunks[0] is chunk1


def test_assemble_respects_max_tokens() -> None:
    chunk1 = Chunk(id=1, content="short content")
    chunk2 = Chunk(id=2, content="very very very long content")

    results = [
        RetrievalResult(chunk=chunk1, score=0.9),
        RetrievalResult(chunk=chunk2, score=0.8),
    ]

    # We set a token estimator that returns the exact length of the text.
    # The formatted chunk1 text is:
    # "---\nDocument: Unknown\nContent:\nshort content\n" (45 chars)
    # The formatted chunk2 text is:
    # "---\nDocument: Unknown\nContent:\nvery very very long content\n" (59 chars)
    assembler = ContextAssembler(max_tokens=50, token_estimator=len)
    assembled = assembler.assemble(results)

    # Adding chunk1 takes 45 tokens. Adding chunk2 would take 45 + 59 = 104, which exceeds 50.
    # Therefore, only chunk1 should be included.
    assert assembled.total_chunks == 1
    assert assembled.chunks[0] is chunk1
    assert assembled.total_tokens == 45


def test_assemble_fallback_document_path() -> None:
    # Chunk with no document object populated
    chunk = Chunk(id=1, content="some code content")
    results = [RetrievalResult(chunk=chunk, score=0.9)]

    assembler = ContextAssembler()
    assembled = assembler.assemble(results)

    assert "Document: Unknown" in assembled.context_str
