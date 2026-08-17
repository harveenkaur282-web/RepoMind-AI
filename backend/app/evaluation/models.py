from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationSample(BaseModel):
    """Pydantic model representing a single evaluation question and its ground truth."""

    id: str = Field(..., description="Unique identifier for the evaluation sample")
    question: str = Field(..., description="The user question or query")
    relevant_documents: list[str] = Field(
        ...,
        description="List of relative paths to relevant files inside the repo",
    )
    relevant_chunks: list[str] = Field(
        default_factory=list,
        description="Optional list of code snippets or content fragments that must match",
    )
    category: str = Field(
        ...,
        description=(
            "Category of question (technical_terms, conceptual, implementation, location, semantic)"
        ),
    )
    difficulty: str = Field(..., description="Difficulty level (easy, medium, hard)")
    repository_name: str = Field(
        ...,
        description="Source repository name (e.g. harveenkaur282-web/RepoMind-AI)",
    )


class EvaluationDataset(BaseModel):
    """Pydantic model representing a collection of evaluation samples."""

    version: str = Field(..., description="Version of the evaluation dataset")
    samples: list[EvaluationSample]
