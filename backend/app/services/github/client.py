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
            headers["Authorization"] = f"Bearer {settings.github_token}"

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

    async def close(self) -> None:
        await self.client.aclose()
