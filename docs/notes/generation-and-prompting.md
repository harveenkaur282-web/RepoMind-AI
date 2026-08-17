# Learning Notes: Generation & Prompting

These notes cover our integration observations with local LLMs and error boundaries.

---

## 1. Ollama Provider Interface
*   Communicates with the local Ollama server on `http://localhost:11434` using the `/api/chat` endpoint.
*   By default, queries `qwen2.5-coder:7b` (a lightweight but state-of-the-art model for local codebase reasoning).

---

## 2. Error Boundary Design
To prevent raw connection errors (e.g. `httpx.ConnectError` or JSON key missing errors) from bubbling up and crashing the RAG service, we created a provider-specific custom exception `LLMProviderError`.

All API communication blocks catch:
*   `httpx.RequestError` (server down, timeouts)
*   `KeyError` / `TypeError` (malformed JSON format response from Ollama)
And map them cleanly into `LLMProviderError` so callers can catch and display human-readable notifications.

---

## 3. Prompt Layout
*   We kept prompt layout minimalistic inside `OllamaProvider`.
*   The system prompt establishes the persona of a senior developer explaining code blocks clearly and concisely.
*   **Context format**: Context is separated by paths, which helps the LLM locate exact source origins:
    ```markdown
    ---
    File: backend/app/main.py
    ---
    [content]
    ```
*   *Observation*: Structuring code chunks with clear file headers significantly increases the model's accuracy when referencing where variables or endpoints are defined.
