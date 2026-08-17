import base64
from typing import Any

import httpx

from backend.app.core.config import get_settings
from backend.app.services.github.exceptions import (
    GitHubAPIError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from backend.app.services.github.schemas import GitHubRepository


class GitHubClient:
    BASE_URL = "https://api.github.com"
    API_VERSION = "2026-03-10"

    def __init__(self) -> None:
        settings = get_settings()

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
        }

        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=30.0,
        )

    async def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> GitHubRepository:
        response = await self.client.get(
            f"/repos/{owner}/{repo}",
        )

        if response.status_code == 404:
            raise GitHubNotFoundError(f"Repository not found: {owner}/{repo}")

        if response.status_code == 403:
            raise GitHubRateLimitError(f"GitHub API rate limit exceeded for {owner}/{repo}")

        if response.is_error:
            raise GitHubAPIError(
                f"GitHub API request failed with status {response.status_code}: {response.text}"
            )

        data: dict[str, Any] = response.json()

        return GitHubRepository.model_validate(data)

    async def get_authenticated_user(self) -> dict[str, object]:
        response = await self.client.get("/user")

        if response.is_error:
            raise GitHubAPIError(
                f"GitHub authentication failed: {response.status_code}: {response.text}"
            )

        return response.json()

    async def get_repository_tree(
        self, owner: str, repo: str, tree_sha: str, recursive: bool = False
    ) -> dict[str, Any]:
        params = {"recursive": "1" if recursive else "0"}

        response = await self.client.get(
            f"/repos/{owner}/{repo}/git/trees/{tree_sha}", params=params
        )

        if response.status_code == 404:
            raise GitHubNotFoundError(
                f"Tree or repository not found: {owner}/{repo} (SHA: {tree_sha})"
            )

        if response.status_code == 403:
            raise GitHubRateLimitError(f"GitHub API rate limit exceeded for {owner}/{repo}")

        if response.is_error:
            raise GitHubAPIError(
                f"GitHub API request failed with status {response.status_code}: {response.text}"
            )

        return response.json()

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> str:
        params = {"ref": ref} if ref else None

        response = await self.client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params=params,
        )

        if response.status_code == 404:
            raise GitHubNotFoundError(
                f"File not found: {owner}/{repo}/{path} (ref: {ref or 'default'})"
            )

        if response.status_code == 403:
            raise GitHubRateLimitError(f"GitHub API rate limit exceeded for {owner}/{repo}")

        if response.is_error:
            raise GitHubAPIError(
                f"GitHub API request failed with status {response.status_code}: {response.text}"
            )

        data: dict[str, Any] = response.json()

        if data.get("encoding") != "base64":
            raise GitHubAPIError(
                f"Unexpected content encoding for {owner}/{repo}/{path}: {data.get('encoding')}"
            )

        content = data.get("content")
        if not isinstance(content, str):
            raise GitHubAPIError(f"No file content returned for {owner}/{repo}/{path}")

        return base64.b64decode(content).decode("utf-8")

    async def close(self) -> None:
        await self.client.aclose()
