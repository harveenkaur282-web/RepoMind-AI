from backend.app.services.retrieval.service import BM25, tokenize


def test_tokenize_standard_case() -> None:
    text = "Hello, World! BM25 retrieval."
    tokens = tokenize(text)
    assert tokens == ["hello", "world", "bm25", "retrieval"]


def test_tokenize_empty_and_whitespace() -> None:
    assert tokenize("") == []
    assert tokenize("   \n\t   ") == []


def test_bm25_initialize_and_scoring() -> None:
    corpus = [
        ["the", "quick", "brown", "fox"],
        ["jumped", "over", "the", "lazy", "dog"],
        ["the", "dog", "was", "lazy", "but", "friendly"],
    ]

    bm25 = BM25(corpus)
    assert bm25.corpus_size == 3
    assert bm25.avgdl == 5.0
    assert len(bm25.doc_len) == 3
    assert len(bm25.doc_freqs) == 3

    # "lazy" is in doc 1 and doc 2.
    # IDF score for "lazy" should be positive
    assert "lazy" in bm25.idf
    assert bm25.idf["lazy"] > 0

    # Retrieve score for "lazy" in doc 1
    score_doc1 = bm25.get_score(1, ["lazy"])
    # Retrieve score for "lazy" in doc 2
    score_doc2 = bm25.get_score(2, ["lazy"])

    assert score_doc1 > 0
    assert score_doc2 > 0

    # Since doc 1 has length 5 and doc 2 has length 6, "lazy" should score slightly higher in doc 1
    assert score_doc1 > score_doc2


def test_bm25_non_existent_term() -> None:
    corpus = [
        ["hello", "world"]
    ]
    bm25 = BM25(corpus)
    assert bm25.get_score(0, ["missing"]) == 0.0


def test_bm25_empty_corpus_or_avgdl_zero() -> None:
    # Empty corpus
    bm25_empty = BM25([])
    assert bm25_empty.avgdl == 0
    
    # Corpus with only empty documents (so avgdl is 0)
    bm25_zero = BM25([[], []])
    assert bm25_zero.avgdl == 0
    # Scoring should not raise ZeroDivisionError and should return 0.0
    assert bm25_zero.get_score(0, ["test"]) == 0.0


def test_tokenize_none() -> None:
    assert tokenize(None) == []

