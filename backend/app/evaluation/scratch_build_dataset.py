from __future__ import annotations

import json
from pathlib import Path

# Programmatic lists of 250 high-quality developer queries mapped to RepoMind-AI codebase files
DOC_QUERIES = [
    # 1. backend/app/main.py (10 queries)
    {
        "doc": "backend/app/main.py",
        "queries": [
            "What is the entrypoint file for the FastAPI application?",
            "How is CORS middleware configured in the FastAPI main application?",
            "Where are the routers included in the FastAPI app instance?",
            "What title and version is assigned to the FastAPI app instance?",
            "How does the backend mount routers or register sub-routers?",
            "Is there an overall startup hook or event listener registered in main.py?",
            "How are API endpoints prefixed or grouped under v1?",
            "What middleware is added to allow Streamlit client requests?",
            "Where does FastAPI initialize its main app object?",
            "Does main.py import any settings or configuration directly?",
        ],
        "category": "location",
        "difficulty": "easy",
    },
    # 2. backend/app/core/config.py (15 queries)
    {
        "doc": "backend/app/core/config.py",
        "queries": [
            "How is the Settings class defined using Pydantic BaseSettings?",
            "Where is the default PostgreSQL database connection string defined?",
            "What default model is configured for Ollama code generation?",
            "What is the default Ollama server URL configured in settings?",
            "Where are Voyage AI embedding and reranker model names configured?",
            "How does settings handle env files and case sensitivity?",
            "What environment variables configure OpenRouter, Gemini, and Groq API keys?",
            "Where is the get_settings function cached using lru_cache?",
            "What is the default model name for Groq and Gemini providers?",
            "Does settings support Redis URL configuration?",
            "Is github_token configured with a default value in config.py?",
            "How can I customize settings using an env file name?",
            "What is the default embedding model name defined in core configuration?",
            "Where is the app_name string defined in Settings?",
            "What config parameters manage the local cross encoder reranking limit?",
        ],
        "category": "configuration",
        "difficulty": "medium",
    },
    # 3. backend/app/db/dependencies.py & session.py (10 queries)
    {
        "doc": "backend/app/db/dependencies.py",
        "queries": [
            "How is the async database session yield handled in get_db?",
            "Where is the FastAPI dependency get_db declared?",
            "How does session.py create the async engine and sessionmaker?",
            "What driver is used for async database connections in RepoMind?",
            "How does the database dependency clean up or close sessions after calls?",
            "Is get_db bound to scoped sessions or fresh instances?",
            "How is async_session_maker configured to expire_on_commit?",
            "Where does SQLALchemy bind the async engine in session.py?",
            "What is the default pool size or connection limit for asyncpg engine?",
            "How are session transaction rollbacks handled in case of exceptions?",
        ],
        "category": "implementation",
        "difficulty": "medium",
    },
    # 4. backend/app/db/models/ (25 queries)
    {
        "doc": "backend/app/db/models/document.py",
        "queries": [
            "How is the relationship between Repository and Document models declared?",
            "Where is the Chunk model schema defined in the database folder?",
            "What column stores the high-dimensional embeddings for chunks?",
            "How does cascade delete orphan configuration clean up chunk vectors?",
            "What indexes are defined on Document and Chunk tables for fast queries?",
            "What data type represents the primary key IDs in Repository model?",
            "How is document path stored in the Document schema?",
            "Where are the mapped SQLAlchemy models defined?",
            "How is the vector dimension size of pgvector defined in Chunk model?",
            "Is there a unique constraint on repository clone URLs?",
            "How are documents associated with their respective repository parent ID?",
            "What fields does the Chunk model have other than content and embedding?",
            "Does the Document table store git blob SHA values?",
            "Where is the back_populates relationship for chunks specified?",
            "How is pgvector Vector class imported in SQLAlchemy models?",
            "Is there a created_at or updated_at timestamp in Repository schema?",
            "What is the maximum length of repository clone URL string?",
            "How is repository owner and name stored in the database?",
            "What fields in Chunk model refer back to Document and Repository?",
            "Are there foreign key constraints on the Document and Chunk tables?",
            "Where is the primary key defined for Chunk model?",
            "What SQLAlchemy class represents the Document model?",
            "Does repository ingestion record the default branch name?",
            "How is document content length or size tracked?",
            "What is the relationship between Chunk and Document in database models?",
        ],
        "category": "conceptual",
        "difficulty": "medium",
    },
    # 5. backend/app/api/v1/endpoints/health.py & repositories.py (20 queries)
    {
        "doc": "backend/app/api/v1/endpoints/health.py",
        "queries": [
            "Where is the server diagnostics health check endpoint defined?",
            "What database metrics and table row counts does diagnostics report?",
            "Where is the GET /api/v1/health route registered?",
            "How is the database connection status checked in health route?",
            "What JSON response format is returned by health check diagnostics?",
            "How do we check if Ollama is running from health checks?",
            "Does diagnostics route execute any raw SQL count commands?",
            "What metrics are returned for repositories, documents, and chunks count?",
            "How are SQLAlchemy exceptions handled in the health diagnostics endpoint?",
            "Where is the ping check logic for Ollama model status?",
        ],
        "category": "location",
        "difficulty": "easy",
    },
    {
        "doc": "backend/app/api/v1/endpoints/repositories.py",
        "queries": [
            "Where is the endpoint to list all ingested repositories defined?",
            "How is the DELETE /api/v1/repositories/{id} route implemented?",
            "What route triggers the cascading deletion of a repository?",
            "How are repositories fetched with async sessions in API routes?",
            "What response payload format is returned when a repository is deleted?",
            "Is there a GET route to retrieve a single repository by ID?",
            "How are API route requests validated for repository deletions?",
            "Where are repository endpoint parameters defined?",
            "Does listing repositories return document counts or total chunks?",
            "How are repository IDs parsed from request paths in api routes?",
        ],
        "category": "location",
        "difficulty": "easy",
    },
    # 6. backend/app/api/v1/endpoints/ingestion.py (20 queries)
    {
        "doc": "backend/app/api/v1/endpoints/ingestion.py",
        "queries": [
            "Where is the REST endpoint for repository ingestion defined?",
            "How is the incremental repository update route POST v1 ingestion implemented?",
            "What request parameters are needed to trigger ingestion updates?",
            "How is the RepositoryIngestor service instantiated in API routes?",
            "What exceptions are caught when repository ingestion fails?",
            "Does ingestion route run asynchronously or block the request thread?",
            "How does the ingestion endpoint validate clone URLs or owner/repo format?",
            "Where are GitHub tokens resolved in ingestion routes?",
            "What JSON structure is returned after a successful repository sync?",
            "Is there a rate limiting protection on the repository ingestion routes?",
            "How does POST ingestion update route resolve repository ID?",
            "Where is the update_repository method called from the API layer?",
            "Does the ingestion endpoint return the count of files updated?",
            "How are DB session commits triggered after ingestion finishes?",
            "Where is the repository clone url parsed in ingestion api?",
            "What dependencies are injected into the ingestion route handler?",
            "How is the GitHub API client authorized inside ingestion routes?",
            "Does ingestion API support custom branch names as parameters?",
            "What HTTP error code is returned if repository to update does not exist?",
            "Where are the FastAPI routing prefixes defined for ingestion?",
        ],
        "category": "location",
        "difficulty": "easy",
    },
    # 7. backend/app/api/v1/endpoints/rag.py (30 queries)
    {
        "doc": "backend/app/api/v1/endpoints/rag.py",
        "queries": [
            "Where is the API endpoint to run a RAG query defined?",
            "How is the query_rag route POST /rag/query implemented?",
            "What parameters does the query_rag endpoint accept?",
            "How is prompt_strategy validated inside the query_rag endpoint?",
            "Where is get_llm_provider called in RAG query routes?",
            "How does POST /rag/query resolve query rewriting options?",
            "Where is VoyageEmbeddingProvider instantiated in the RAG route?",
            "What is the POST /rag/compare endpoint used for?",
            "How does the compare route retrieve chunks for multiple strategies?",
            "Does compare endpoint run dense, BM25, and hybrid search side-by-side?",
            "What response payload format is returned by compare retrieval route?",
            "How is the query embedded before calling retrieval in rag endpoints?",
            "Where are HTTPExceptions raised for failed query embeddings?",
            "How are document_id and repository_id filters passed to rag routes?",
            "What JSON format lists matching chunks with original and rerank scores?",
            "How is the default prompt strategy configured in the RAG API router?",
            "Does query_rag catch generic exception failures and return HTTP 500?",
            "Where are prompt strategy configurations resolved in endpoints?",
            "Does compare route use LLM providers or just RetrievalService?",
            "How are document paths formatted in chunk dictionaries in RAG API?",
            "What parameters are passed from POST /query route to answer_query?",
            "Where are settings loaded in the RAG endpoint router?",
            "Is there an endpoint that checks the health of LLM connections?",
            "How are original query and rewritten search query structured in response?",
            "How are database dependency session bindings injected in RAG routes?",
            "Where is the system prompt fetched in the query_rag handler?",
            "What is the structure of the RAG compare JSON output?",
            "Does POST /query accept a custom rerank boolean parameter?",
            "How is rerank_limit parsed from query parameters in API routes?",
            "Are CORS origins allowed for RAG query and compare endpoints?",
        ],
        "category": "location",
        "difficulty": "easy",
    },
    # 8. backend/app/services/embeddings/ (15 queries)
    {
        "doc": "backend/app/services/embeddings/voyage.py",
        "queries": [
            "How is VoyageEmbeddingProvider implemented using VoyageAI client?",
            "What method is defined in EmbeddingProvider protocol for query embedding?",
            "What embedding model name is passed to Voyage client by default?",
            "How are document chunks embedded in batches in Voyage provider?",
            "How are exceptions handled if the Voyage AI API call fails?",
            "Where is VoyageEmbeddingProvider defined in services?",
            "What API key variable is required by VoyageEmbeddingProvider?",
            "Does VoyageEmbeddingProvider implement async embed_query and embed_documents?",
            "How does the embedding service handle API rate limit retry backoffs?",
            "What dimension size is returned by Voyage code embeddings?",
            "Is there a protocol interface class for embedding providers?",
            "How is the Voyage client instantiated with API keys in provider?",
            "Does embed_documents accept a list of strings and return list of lists?",
            "How is the base embedding service module structured?",
            "Where can I customize the embedding model parameter in code?",
        ],
        "category": "implementation",
        "difficulty": "medium",
    },
    # 9. backend/app/services/generation/ (30 queries)
    {
        "doc": "backend/app/services/generation/factory.py",
        "queries": [
            "How does get_llm_provider select the provider from Settings?",
            "Where is validate_llm_settings defined in generation layer?",
            "How are API keys validated for OpenRouter, Gemini, and Groq?",
            "Does Ollama require an API key validation check in factory?",
            "What exception is raised if a required API key is missing?",
            "How is GeminiProvider instantiated in the factory?",
            "Where are Groq and OpenRouter providers loaded and configured?",
            "How does OllamaProvider communicate with local Ollama url?",
            "What base protocol class represents LLMProvider interface?",
            "Is LLMProviderError used to normalize all provider connection failures?",
            "How is the generation model name configured per provider?",
            "Where is the async request completion method defined for LLMs?",
            "How does GroqProvider handle completions using httpx client?",
            "What API URL is used by GroqProvider completions endpoint?",
            "How does GeminiProvider initialize Google GenerativeAI API key?",
            "Does OpenRouterProvider support custom models in completion request?",
            "How are authorization headers structured in OpenRouter requests?",
            "Where is httpx.AsyncClient timeout configured for LLM providers?",
            "How does OllamaProvider handle malformed JSON responses?",
            "What is the system prompt mapping structure inside LLM request body?",
            "Does the generation layer log or print sensitive API keys?",
            "Where is the completion response parsed in OpenRouterProvider?",
            "How does GeminiProvider map generation config parameters?",
            "What is the default completion model for OpenRouter in code?",
            "How are provider errors translated into LLMProviderError?",
            "Where are tests for generation providers and factory validation?",
            "Does get_llm_provider fall back to Ollama if settings are unknown?",
            "How are JSON payload formats structured for Groq completions?",
            "Is there an async close connection method for LLM providers?",
            "Does the factory validation check settings before provider setup?",
        ],
        "category": "implementation",
        "difficulty": "medium",
    },
    # 10. backend/app/services/ingestion/repository_ingestor.py (20 queries)
    {
        "doc": "backend/app/services/ingestion/repository_ingestor.py",
        "queries": [
            "How does RepositoryIngestor check file updates using Git blob SHAs?",
            "Where is the file parsing and text chunking logic triggered during ingestion?",
            "How does the ingestion process skip unchanged documents in RepoMind?",
            "What method inside RepositoryIngestor removes deleted repo files?",
            "How does incremental update determine if a file is modified?",
            "Where is the GitHub client instantiated inside RepositoryIngestor?",
            "How are Voyage embeddings generated for new document chunks?",
            "What chunking strategy is used by default for repo code files?",
            "How are documents saved and mapped to Chunk rows in database?",
            "What exceptions are thrown if Git tree fetching fails?",
            "How is the repository record initialized in database on first sync?",
            "Does RepositoryIngestor run file classification to filter binary files?",
            "Where is the batch size configured for chunk embedding ingestion?",
            "How are document aware chunks mapped to pgvector columns?",
            "What happens to existing chunks in DB when a file is modified?",
            "How are document records linked to repository records in database?",
            "Does the ingestor support updating specific files instead of entire repo?",
            "What branch is cloned by default if branch parameter is omitted?",
            "How does the ingestor handle empty repositories or folders?",
            "Where is transaction management handled in repository ingestion service?",
        ],
        "category": "implementation",
        "difficulty": "hard",
    },
    # 11. backend/app/services/rag/prompts.py & rewriter.py & reranker/ (35 queries)
    {
        "doc": "backend/app/services/rag/prompts.py",
        "queries": [
            "What distinct system prompts are defined in prompts.py?",
            "How is the concise_grounded prompt strategy structured in code?",
            "Where is get_system_prompt defined in RAG services?",
            "What instruction does the detailed_grounded prompt give to the LLM?",
            "How does developer_assistant strategy prompt handle file paths?",
            "What error is raised if an invalid prompt strategy name is passed?",
            "Where is the PROMPT_STRATEGIES dictionary defined in prompts?",
            "Are system prompts token efficient or highly verbose?",
            "How does the system prompt warn LLMs about lack of context?",
        ],
        "category": "conceptual",
        "difficulty": "easy",
    },
    {
        "doc": "backend/app/services/rag/rewriter.py",
        "queries": [
            "What is the system prompt used by QueryRewriter?",
            "How does QueryRewriter optimize a natural language search query?",
            "Where is QueryRewriter class defined in RAG folder?",
            "What method is called on LLMProvider by the QueryRewriter?",
            "How are quotes and whitespace stripped from rewritten queries?",
            "What exception is thrown if query rewriting fails in rewriter?",
            "Is there a standalone test file for testing QueryRewriter?",
            "Does QueryRewriter query database or just rewrite text?",
            "What parameters are passed to generate in QueryRewriter.rewrite?",
        ],
        "category": "conceptual",
        "difficulty": "medium",
    },
    {
        "doc": "backend/app/services/rag/reranker/local.py",
        "queries": [
            "How does LocalCrossEncoderReranker tokenize search queries?",
            "What method is defined in Reranker Protocol interface?",
            "How does CamelCase and snake_case splitting work in local reranker?",
            "Where is path matching boost score calculated in reranker?",
            "How does local reranker compute term overlap intersection?",
            "What phrase match bonus score is added for matching token sequences?",
            "How does LocalCrossEncoderReranker sort candidates descending?",
            "Are empty candidate lists supported by local reranker method?",
            "Where is rerank_score attribute populated on RetrievalResult?",
            "What settings configuration controls the local reranker model name?",
            "How is the reranker class instantiated in API endpoints?",
            "Does the local reranker require torch, transformers, or external APIs?",
            "How are scores clamped between zero and one in local reranker?",
            "Where are unit tests validating cross encoder reordering order?",
            "Is there a candidate limit applied before calling rerank method?",
            "What regex pattern is used to break camelCase in tokenize?",
            "Does local reranker fall back to vector search scores on tie?",
        ],
        "category": "implementation",
        "difficulty": "hard",
    },
    # 12. backend/app/services/rag/service.py (15 queries)
    {
        "doc": "backend/app/services/rag/service.py",
        "queries": [
            "How does RAGService orchestrate query, retrieval, and generation?",
            "What properties are defined on the RAGResponse dataclass?",
            "Where is the search_query parameter resolved in answer_query?",
            "How is the larger candidate pool limit passed to RetrievalService?",
            "Where is the reranker called inside the RAGService pipeline?",
            "How are reranked results sliced back to top_k final size?",
            "What parameters are passed to RetrievalService.search in service?",
            "Where is the context assembler called in RAGService flow?",
            "How is the generated LLM response returned in RAGResponse?",
            "What happens if rerank is enabled but no reranker is set?",
            "How are token count and strategy fields populated in response?",
            "Does RAGService constructor accept an optional reranker parameter?",
            "Is the original query preserved for the generation step?",
            "How does RAGService handle query rewriting configuration?",
            "Where is the prompt_strategy passed to the generation provider?",
        ],
        "category": "architecture",
        "difficulty": "hard",
    },
    # 13. backend/app/services/retrieval/context.py & service.py (25 queries)
    {
        "doc": "backend/app/services/retrieval/context.py",
        "queries": [
            "How does ContextAssembler deduplicate chunk results by ID?",
            "Where are retrieved chunks formatted into structured strings?",
            "How is the max_tokens limit enforced in ContextAssembler?",
            "What default token estimator callable is used if none is provided?",
            "What properties does the AssembledContext dataclass contain?",
            "How is chunk document path included in formatted context string?",
            "Is character length division used to estimate token sizes?",
            "Where is max_chunks configuration parameter checked in assembly?",
            "Does ContextAssembler preserve original retrieval ranking order?",
            "How is context formatting prefix styled for file headers?",
        ],
        "category": "conceptual",
        "difficulty": "medium",
    },
    {
        "doc": "backend/app/services/retrieval/service.py",
        "queries": [
            "How does RetrievalService execute dense similarity searches?",
            "Where is the Reciprocal Rank Fusion RRF algorithm implemented?",
            "What constant weight value is added to ranks in RRF scoring?",
            "How does BM25 score chunks based on token frequency?",
            "What tokenizer regex pattern is used in BM25 term parsing?",
            "Where is Inverse Document Frequency IDF calculated for BM25?",
            "How does retrieval service handle repository_id filters?",
            "What strategies are supported in RetrievalService.search?",
            "How are database queries async executed in RetrievalService?",
            "What is the mathematical definition of RRF score in retrieval?",
            "Does BM25 search calculate average document length for corpus?",
            "How are dense vector similarity distances calculated in pgvector?",
            "Where is RetrievalResult dataclass defined in codebase?",
            "What is the default top_k parameter value in search?",
            "Does RetrievalService handle document_id level search filtering?",
        ],
        "category": "implementation",
        "difficulty": "hard",
    },
]


def generate_dataset_file() -> None:
    samples = []
    question_counter = 1

    for item in DOC_QUERIES:
        doc_path = item["doc"]
        queries = item["queries"]
        category = item["category"]
        difficulty = item["difficulty"]

        for q in queries:
            # Construct a clean EvaluationSample
            sample_id = f"eval-{question_counter:03d}"
            # Extract basic relevant chunks based on doc type
            chunk_keywords = []
            if "service.py" in doc_path:
                chunk_keywords = ["class RAGService", "def answer_query"]
            elif "config.py" in doc_path:
                chunk_keywords = ["class Settings", "get_settings"]
            elif "local.py" in doc_path:
                chunk_keywords = ["class LocalCrossEncoderReranker", "def rerank"]
            elif "rewriter.py" in doc_path:
                chunk_keywords = ["class QueryRewriter", "def rewrite"]
            elif "prompts.py" in doc_path:
                chunk_keywords = ["PROMPT_STRATEGIES", "def get_system_prompt"]
            elif "main.py" in doc_path:
                chunk_keywords = ["app = FastAPI", "cors"]
            else:
                chunk_keywords = ["class", "def"]

            samples.append(
                {
                    "id": sample_id,
                    "question": q,
                    "relevant_documents": [doc_path],
                    "relevant_chunks": chunk_keywords,
                    "category": category,
                    "difficulty": difficulty,
                    "repository_name": "harveenkaur282-web/RepoMind-AI",
                }
            )
            question_counter += 1

    dataset = {
        "version": "2.0.0",
        "samples": samples,
    }

    project_root = Path(__file__).parents[3]
    output_dir = project_root / "evaluation" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "retrieval_dataset_v2.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Programmatically generated {len(samples)} questions in {output_path}")


if __name__ == "__main__":
    generate_dataset_file()
