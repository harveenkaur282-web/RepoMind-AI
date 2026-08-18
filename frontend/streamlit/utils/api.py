from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


def get_api_timeout_seconds() -> float:
    for key in ("FASTAPI_TIMEOUT_SECONDS", "REPO_MIND_API_TIMEOUT_SECONDS"):
        value = os.getenv(key)
        if value:
            try:
                return float(value)
            except ValueError:
                continue

    try:
        for key in ("FASTAPI_TIMEOUT_SECONDS", "REPO_MIND_API_TIMEOUT_SECONDS"):
            value = st.secrets.get(key)
            if value:
                return float(value)
    except Exception:
        pass

    return 180.0


def get_api_base_url() -> str:
    env_keys = ("FASTAPI_BASE_URL", "REPO_MIND_API_BASE_URL")

    for key in env_keys:
        value = os.getenv(key)
        if value:
            return value.rstrip("/")

    try:
        for key in env_keys:
            value = st.secrets.get(key)
            if value:
                return str(value).rstrip("/")
    except Exception:
        pass

    raise ValueError(
        "FastAPI base URL is not configured. Set FASTAPI_BASE_URL or "
        "define it in .streamlit/secrets.toml."
    )


def _request_json(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    base_url = get_api_base_url()
    url = f"{base_url}{path}"
    timeout = get_api_timeout_seconds()

    try:
        response = httpx.request(method=method, url=url, timeout=timeout, **kwargs)
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "The backend request timed out. Large repositories can take "
            "longer to ingest, so the API may need more time."
        ) from exc

    if response.is_error:
        detail = response.text
        try:
            payload = response.json()
            detail = payload.get("detail", detail)
        except ValueError:
            pass
        raise RuntimeError(f"API request failed: {detail}")

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("The API returned a non-JSON response.") from exc


def get_health() -> dict[str, str]:
    return _request_json("GET", "/api/v1/health")


def ingest_repository(owner: str, repo: str) -> dict[str, Any]:
    return _request_json(
        "POST",
        "/api/v1/ingestion/repository",
        params={"owner": owner, "repo": repo},
    )


def get_repositories() -> list[dict[str, Any]]:
    data = _request_json("GET", "/api/v1/repositories")
    if not isinstance(data, list):
        raise RuntimeError("The repository list endpoint returned a non-list response.")
    return data


def query_rag(
    query: str,
    strategy: str = "dense",
    repository_id: int | None = None,
) -> dict[str, Any]:
    params = {
        "query": query,
        "strategy": strategy,
    }
    if repository_id is not None:
        params["repository_id"] = repository_id

    return _request_json(
        "POST",
        "/api/v1/rag/query",
        params=params,
    )


def delete_repository(repository_id: int) -> None:
    base_url = get_api_base_url()
    url = f"{base_url}/api/v1/repositories/{repository_id}"
    timeout = get_api_timeout_seconds()

    response = httpx.delete(url, timeout=timeout)
    if response.is_error:
        detail = response.text
        try:
            payload = response.json()
            detail = payload.get("detail", detail)
        except ValueError:
            pass
        raise RuntimeError(f"API request failed: {detail}")


def update_repository(repository_id: int) -> dict[str, Any]:
    return _request_json(
        "POST",
        f"/api/v1/ingestion/repository/{repository_id}/update",
    )


def get_diagnostics() -> dict[str, Any]:
    return _request_json("GET", "/api/v1/health/diagnostics")


def compare_retrieval(query: str, repository_id: int | None = None) -> dict[str, Any]:
    params = {"query": query}
    if repository_id is not None:
        params["repository_id"] = repository_id
    return _request_json("POST", "/api/v1/rag/compare", params=params)


def submit_feedback(
    request_id: str,
    rating: str,
    feedback_text: str | None = None,
) -> dict[str, Any]:
    return _request_json(
        "POST",
        "/api/v1/feedback",
        json={
            "request_id": request_id,
            "rating": rating,
            "feedback_text": feedback_text,
        },
    )
