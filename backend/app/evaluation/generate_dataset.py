from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.config import get_settings
from backend.app.db.models.document import Document
from backend.app.db.session import AsyncSessionLocal
from backend.app.evaluation.models import EvaluationDataset, EvaluationSample
from backend.app.services.generation.factory import get_llm_provider


async def generate_evaluation_questions(
    db: AsyncSession,
    llm_provider,
    questions_per_doc: int = 4,
) -> list[EvaluationSample]:
    """Generate realistic developer questions for each document in the database using LLM."""
    result = await db.execute(select(Document))
    documents = result.scalars().all()

    if not documents:
        print("No documents found in the database. Please ingest a repository first.")
        return []

    samples = []
    question_id_counter = 1
    seen_questions = set()

    system_prompt = (
        "You are an expert software engineer. Given a code file, generate a list of "
        "realistic developer questions. The questions should cover conceptual architecture, "
        "implementation details, debugging, location of features, and configuration. "
        "Do NOT mention the filename or relative paths directly in the questions to avoid leakage. "
        'Respond with a plain JSON list of strings, for example: ["Question 1", "Question 2"].'
    )

    for doc in documents:
        # Get content preview (limit to fit token budgets)
        content_preview = ""
        for chunk in doc.chunks:
            content_preview += chunk.content + "\n"
        content_preview = content_preview[:4000]

        if not content_preview.strip():
            continue

        query = (
            f"Generate exactly {questions_per_doc} realistic developer questions "
            f"about this code:\n\n{content_preview}"
        )

        try:
            response = await llm_provider.generate(
                context="",
                query=query,
                system_prompt=system_prompt,
            )

            # Clean and parse JSON response
            cleaned_response = response.strip()
            # Handle markdown code blocks
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0]
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0]

            questions = json.loads(cleaned_response)

            # Map categories based on question keywords
            for q in questions:
                q_clean = q.strip().strip('"').strip("'")
                if not q_clean or q_clean in seen_questions:
                    continue
                seen_questions.add(q_clean)

                # Classify question category
                category = "conceptual"
                lower_q = q_clean.lower()
                if "where" in lower_q or "file" in lower_q or "define" in lower_q:
                    category = "location"
                elif "how" in lower_q or "implement" in lower_q or "write" in lower_q:
                    category = "implementation"
                elif (
                    "bug" in lower_q
                    or "error" in lower_q
                    or "fail" in lower_q
                    or "exception" in lower_q
                ):
                    category = "debugging"
                elif "configure" in lower_q or "settings" in lower_q or "env" in lower_q:
                    category = "configuration"
                elif "design" in lower_q or "architecture" in lower_q or "flow" in lower_q:
                    category = "architecture"

                # Assign difficulty
                difficulty = "medium"
                if len(q_clean.split()) < 7:
                    difficulty = "easy"
                elif len(q_clean.split()) > 15:
                    difficulty = "hard"

                # Generate chunk references if any match
                relevant_chunks = []
                for chunk in doc.chunks:
                    # If query has matching words in chunk, add fragment
                    words = set(re.findall(r"\w+", q_clean.lower()))
                    chunk_words = set(re.findall(r"\w+", chunk.content.lower()))
                    if len(words.intersection(chunk_words)) > 3:
                        relevant_chunks.append(chunk.content[:100])
                        break

                samples.append(
                    EvaluationSample(
                        id=f"eval-{question_id_counter:03d}",
                        question=q_clean,
                        relevant_documents=[doc.path],
                        relevant_chunks=relevant_chunks[:3],
                        category=category,
                        difficulty=difficulty,
                        repository_name=doc.repository.name if doc.repository else "unknown",
                    )
                )
                question_id_counter += 1

        except Exception as exc:
            print(f"Failed to generate questions for {doc.path}: {exc}")

    return samples


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="evaluation/data/retrieval_dataset_v2.json")
    parser.add_argument("--count", type=int, default=4)
    args = parser.parse_args()

    settings = get_settings()
    llm_provider = get_llm_provider(settings)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as session:
        print("Starting evaluation dataset generation...")
        samples = await generate_evaluation_questions(session, llm_provider, args.count)

        if not samples:
            print("No questions generated.")
            return

        dataset = EvaluationDataset(version="2.0.0", samples=samples)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset.model_dump(), f, indent=2)

        print(f"Successfully generated {len(samples)} questions and saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
