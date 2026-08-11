import pytest

from backend.app.services.github.client import GitHubClient


@pytest.mark.asyncio
async def test_get_repository() -> None:
    client = GitHubClient()

    try:
        repository = await client.get_repository(
            "octocat",
            "Hello-World",
        )

        assert repository.name == "Hello-World"
        assert repository.owner.login == "octocat"
        assert repository.html_url.startswith("https://github.com/")
        assert repository.default_branch

    finally:
        await client.close()

@pytest.mark.asyncio
async def test_authenticated_user() -> None:
    client = GitHubClient()

    try:
        user = await client.get_authenticated_user()

        assert user["login"]
        assert user["id"]

    finally:
        await client.close()
