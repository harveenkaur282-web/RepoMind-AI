from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.evaluation.models import EvaluationDataset, EvaluationSample


def test_evaluation_dataset_schema_and_loading() -> None:
    # 1. Resolve path to versioned dataset JSON file
    project_root = Path(__file__).parents[3]
    dataset_path = project_root / "evaluation" / "data" / "retrieval_dataset_v1.json"

    assert dataset_path.exists(), f"Dataset file not found at: {dataset_path}"

    # 2. Load file and validate with Pydantic schema
    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)

    dataset = EvaluationDataset.model_validate(data)

    # 3. Assertions on dataset structure and content
    assert dataset.version == "1.0.0"
    assert len(dataset.samples) == 5

    # Check a specific sample
    sample = dataset.samples[0]
    assert sample.id == "eval-001"
    assert sample.question == "What parameters does the answer_query method in RAGService accept?"
    assert sample.relevant_documents == ["backend/app/services/rag/service.py"]
    assert "async def answer_query(" in sample.relevant_chunks
    assert sample.category == "technical_terms"
    assert sample.difficulty == "easy"
    assert sample.repository_name == "harveenkaur282-web/RepoMind-AI"


def test_evaluation_sample_validation_fails_on_missing_fields() -> None:
    # Test that missing required fields raises a ValidationError
    invalid_data = {
        "id": "eval-fail",
        "question": "Vague question?",
        # Missing relevant_documents, category, etc.
    }

    with pytest.raises(ValidationError):
        EvaluationSample.model_validate(invalid_data)


def test_evaluation_dataset_v2_validation() -> None:
    # 1. Resolve path to versioned dataset JSON file
    project_root = Path(__file__).parents[3]
    dataset_path = project_root / "evaluation" / "data" / "retrieval_dataset_v2.json"

    assert dataset_path.exists(), f"Dataset file not found at: {dataset_path}"

    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)

    dataset = EvaluationDataset.model_validate(data)

    assert dataset.version == "2.0.0"
    assert 250 <= len(dataset.samples) <= 300

    questions = []
    for sample in dataset.samples:
        # Verify required fields
        assert sample.id.startswith("eval-")
        assert len(sample.question.strip()) > 0
        assert len(sample.relevant_documents) > 0

        # Verify no empty paths
        for doc in sample.relevant_documents:
            assert len(doc.strip()) > 0
            # Validate that paths point to valid paths inside the codebase
            doc_file = project_root / doc
            assert doc_file.exists() or doc.endswith(".py"), f"Document file does not exist: {doc}"

        assert sample.category in (
            "technical_terms",
            "conceptual",
            "implementation",
            "location",
            "semantic",
            "debugging",
            "configuration",
            "architecture",
        )
        assert sample.difficulty in ("easy", "medium", "hard")
        assert len(sample.repository_name.strip()) > 0

        questions.append(sample.question.lower().strip())

    # Verify no duplicate questions
    assert len(questions) == len(set(questions)), (
        "Found duplicate questions in the evaluation dataset!"
    )


def test_calculate_hit_rate() -> None:
    from backend.app.evaluation.evaluate_retrieval import calculate_hit_rate

    # Match in list
    assert calculate_hit_rate(["a.py", "b.py"], ["b.py"]) == 1.0
    # No match
    assert calculate_hit_rate(["a.py", "b.py"], ["c.py"]) == 0.0
    # Empty
    assert calculate_hit_rate([], ["a.py"]) == 0.0


def test_calculate_mrr() -> None:
    from backend.app.evaluation.evaluate_retrieval import calculate_mrr

    # Match at rank 1
    assert calculate_mrr(["a.py", "b.py"], ["a.py"]) == 1.0
    # Match at rank 2
    assert calculate_mrr(["a.py", "b.py"], ["b.py"]) == 0.5
    # No match
    assert calculate_mrr(["a.py", "b.py"], ["c.py"]) == 0.0
    # Empty
    assert calculate_mrr([], ["a.py"]) == 0.0


def test_calculate_recall() -> None:
    from backend.app.evaluation.evaluate_retrieval import calculate_recall

    # Complete match
    assert calculate_recall(["a.py", "b.py"], ["a.py", "b.py"]) == 1.0
    # Partial match
    assert calculate_recall(["a.py", "c.py"], ["a.py", "b.py"]) == 0.5
    # No match
    assert calculate_recall(["c.py", "d.py"], ["a.py", "b.py"]) == 0.0
    # Empty retrieved
    assert calculate_recall([], ["a.py"]) == 0.0
    # Empty expected
    assert calculate_recall(["a.py"], []) == 0.0


def test_mrr_mathematical_guarantees() -> None:
    from backend.app.evaluation.evaluate_retrieval import calculate_mrr

    # 1. MRR@10 >= MRR@5 for the same rankings
    ranking = ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py"]
    expected = ["f.py"]

    mrr_5 = calculate_mrr(ranking[:5], expected)
    mrr_10 = calculate_mrr(ranking[:10], expected)

    assert mrr_5 == 0.0  # f.py is at rank 6, so outside top 5
    assert mrr_10 == 1.0 / 6  # f.py is within top 10
    assert mrr_10 >= mrr_5

    # 2. relevant result at rank 1 gives reciprocal rank 1
    assert calculate_mrr(["a.py", "b.py"], ["a.py"]) == 1.0

    # 3. relevant result at rank 5 gives 1/5
    assert calculate_mrr(["a.py", "b.py", "c.py", "d.py", "e.py"], ["e.py"]) == 0.2

    # 4. relevant result at rank 6 contributes to MRR@10 but not MRR@5
    ranking_6 = ["a", "b", "c", "d", "e", "target", "g"]
    assert calculate_mrr(ranking_6[:5], ["target"]) == 0.0
    assert calculate_mrr(ranking_6[:10], ["target"]) == 1.0 / 6

    # 5. no relevant result gives 0
    assert calculate_mrr(["a.py", "b.py"], ["c.py"]) == 0.0
